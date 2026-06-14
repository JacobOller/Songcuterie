# CuratelyFM (Song Finder) — Project Plan

> Last updated: 2026-05-16
> Status: Planning phase

---

## 1. Project Summary

Song Finder is a web app that connects to a user's Spotify account and does two things:

1. **Vibe-based playlist generation** — the user describes a mood or scenario (e.g. "late night drive in the rain") and the app returns a ~10 song playlist that matches the vibe *and* is personalized to their taste.
2. **Music discovery** — the app surfaces new songs and artists the user hasn't heard, using their listening history as a signal, going deeper than Spotify's native algorithm.

---

## 2. User Stories

### Core (MVP)

- As a user, I can log in with my Spotify account so the app can access my listening data.
- As a user, I can type a vibe or mood into a text box and receive a 10-song playlist that matches it.
- As a user, the playlist I receive reflects my personal taste, not just generic matches.
- As a user, I can save a generated playlist directly to my Spotify account.
- As a user, I can see my top artists and tracks from Spotify displayed on my profile page.

### Discovery

- As a user, I can request "find me something new" and receive song recommendations outside my listening history.
- As a user, I can see *why* a song was recommended (e.g. "matches your taste for low-energy acoustic tracks").

### Nice-to-have (post-MVP)

- As a user, I can tweak a generated playlist (swap a song, adjust the vibe) before saving.
- As a user, I can share a generated playlist via a public link.
- TODO: any other features you want to add?

---

## 3. API Endpoints

### Auth


| Method | Endpoint         | Description                                          |
| ------ | ---------------- | ---------------------------------------------------- |
| GET    | `/auth/login`    | Redirects user to Spotify OAuth consent screen       |
| GET    | `/auth/callback` | Handles OAuth redirect, exchanges code for tokens    |
| GET    | `/auth/me`       | Returns current authenticated user's Spotify profile |
| POST   | `/auth/refresh`  | Refreshes expired Spotify access token               |


### User Data


| Method | Endpoint            | Description                                        |
| ------ | ------------------- | -------------------------------------------------- |
| GET    | `/user/top-tracks`  | Returns user's top tracks (short/medium/long term) |
| GET    | `/user/top-artists` | Returns user's top artists                         |
| GET    | `/user/recent`      | Returns recently played tracks                     |


### Search & Generation


| Method | Endpoint           | Description                                        |
| ------ | ------------------ | -------------------------------------------------- |
| POST   | `/search/mood`     | Takes vibe string, returns 10 song recommendations |
| POST   | `/search/discover` | Returns new songs based on user taste profile      |


### Playlist


| Method | Endpoint           | Description                                              |
| ------ | ------------------ | -------------------------------------------------------- |
| POST   | `/playlist/create` | Creates a new Spotify playlist from a list of track URIs |


> TODO: Do you want a `/playlist/preview` endpoint that holds a playlist in-memory before the user decides to save it? Worth thinking about.

---

## 4. Data Schemas

### `Track`

```json
{
  "id": "spotify:track:abc123",
  "name": "Noctuary",
  "artist": "Men I Trust",
  "album": "Untourable Album",
  "duration_ms": 214000,
  "preview_url": "https://...",
  "audio_features": {
    "valence": 0.24,
    "energy": 0.38,
    "danceability": 0.51,
    "acousticness": 0.72,
    "instrumentalness": 0.04,
    "tempo": 98.0
  },
  "popularity": 62
}
```

### `VibeQuery`

```json
{
  "raw_text": "late night drive in the rain",
  "parsed_params": {
    "valence": 0.2,
    "energy": 0.35,
    "acousticness": 0.6,
    "target_genres": ["indie", "ambient", "dream pop"]
  }
}
```

### `Playlist`

```json
{
  "id": "generated_uuid",
  "name": "Late Night Drive",
  "vibe_query": "late night drive in the rain",
  "tracks": ["<Track>", "..."],
  "created_at": "2026-05-16T22:00:00Z",
  "saved_to_spotify": false,
  "spotify_playlist_id": null
}
```

### `UserProfile` (app-internal)

```json
{
  "spotify_id": "user123",
  "display_name": "Alex",
  "top_track_ids": ["...", "..."],
  "top_artist_ids": ["...", "..."],
  "taste_embedding": [0.12, -0.44, "... (vector)"]
}
```

> TODO: Decide how long to cache user data. Options: session-only (simplest), Redis (persistent), or just re-fetch each time.

---

## 5. Architecture

```
/client         → Next.js + TypeScript + Tailwind CSS
/server         → FastAPI + Python
  /routers      → One file per endpoint group (auth, user, search, playlist)
  /services     → Business logic (spotify_client.py, mood_parser.py, recommender.py)
  /models       → Pydantic schemas (Track, Playlist, VibeQuery, etc.)
  /tests        → One test file per router
/brain          → LLM prompt templates + ChromaDB logic
  /prompts      → mood_to_params.txt, discovery.txt
  /embeddings   → Embedding + upsert logic for ChromaDB
.env.example
```

---

## 6. The "Brain" — Mood-to-Music Logic

This is the core of the app. The pipeline for a vibe query is:

```
User text → LLM → Spotify audio feature params → ChromaDB similarity search → Filter by user taste → Return tracks
```

### Step 1: LLM parses the vibe

The raw text (e.g. "late night drive in the rain") is sent to the LLM with a prompt that asks it to output a structured JSON object of Spotify audio feature targets.

**Key audio features to target:**

- `valence` (0–1): musical positiveness. Sad/dark = low, happy/bright = high.
- `energy` (0–1): intensity and activity. Mellow = low, intense = high.
- `acousticness` (0–1): likelihood the track is acoustic.
- `danceability` (0–1): how suitable for dancing.
- `instrumentalness` (0–1): predicts whether a track has no vocals.
- `tempo` (BPM): target tempo range.

### Step 2: ChromaDB vector search

Song embeddings (TODO: define *what* we're embedding — track descriptions? genre tags? audio features themselves?) are queried for similarity against the parsed vibe params.

> **Key decision needed:** What are we embedding?
>
> - Option A: Embed a text description of each track ("melancholic indie pop, slow tempo, female vocals")
> - Option B: Embed the raw audio feature vectors directly
> - Option C: Hybrid — embed both and weight the results
> Recommendation: Start with Option A. It's more natural language-friendly and easier to debug.

### Step 3: Personalization filter

Results from ChromaDB are re-ranked or filtered against the user's top tracks/artists to bias toward their taste.

---

## 7. Environment Variables

```bash
# Spotify
SPOTIFY_CLIENT_ID=
SPOTIFY_CLIENT_SECRET=
SPOTIFY_REDIRECT_URI=http://localhost:3000/auth/callback
 
# LLM (Gemini 2.5 Flash via Google AI Studio)
GOOGLE_API_KEY=
LLM_MODEL=gemini-2.5-flash
 
# App
SECRET_KEY=              # for signing session tokens
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000
 
# ChromaDB
CHROMA_PERSIST_DIR=./brain/chroma_db
 
# TODO: add any others you know you'll need
```

> **Decided: Gemini 2.5 Flash** via Google AI Studio API.
> Cost: $0.15/$0.60 per million input/output tokens. A vibe query (~215 tokens total) costs a fraction of a cent. Expected total dev cost: $0–2. Free tier available for development.

---

## 8. Minimum Viable Product (MVP)

**By end of Week 1**, I should be able to:

- Log in with my Spotify account via OAuth
- See my top artists and tracks rendered on a page I built
**By end of Week 2**, I should be able to:
- Type a vibe into the app and get back a list of 10 tracks (even if the UI is rough)
- See the LLM's parsed audio feature params displayed for debugging
**By end of Week 3**, I should be able to:
- Run a full end-to-end vibe query with ChromaDB powering the search
- See a polished playlist UI with track info, album art, and preview capability
**By end of Week 4 (full MVP)**, I should be able to:
- Log in → describe a vibe → receive a personalized playlist → save it to Spotify
- Demo this end-to-end in a screen recording

---

## 9. Schedule & Milestones

### Week 1 — Infrastructure ✅ Complete

- Spotify Developer Portal app created
- FastAPI project initialized, running on `localhost:8000`
- Next.js project initialized with Tailwind, running on `localhost:3000`
- Folder structure scaffolded (`/client`, `/server`, `/brain`)
- Spotify OAuth 2.0 implemented end-to-end
- `/auth/me` endpoint — user profile displayed in frontend
- Top 20 tracks fetched and rendered
- Cookies storing and persisting user tokens

---

### Week 2 — AI/Logic Engine

- Gemini 2.5 Flash integrated in `brain/`
- Prompt template written: vibe text → structured JSON audio feature params
- `/search/mood` endpoint built in `routers/search.py`
- Debug view in browser showing raw LLM output (parsed params)
- Spotify audio features integrated in `services/spotify_client.py`
- Recommendation logic: LLM params → Spotify recommendations API → 10 tracks returned
- 10 tracks rendered in frontend (rough UI is fine)
- Personalization layer: results re-ranked against user's top artists/genres
- Edge case handling — bad input, API failures, empty results
- LLM prompt refined until results feel accurate
- Tests written for `/search/mood`
- **Demo:** type "late night drive" → see 10 personalized tracks. Commit + push.

---

### Week 3 — Search & Discovery

- ChromaDB installed and configured locally
- Embedding strategy decided (see Section 6)
- First batch of tracks embedded and stored in ChromaDB
- ChromaDB query wired into `/search/mood` flow
- `/search/discover` endpoint built — new tracks outside listening history
- Main playlist UI — album art, track name, artist, 30s preview player
- Discovery UI — "find me something new" flow works end-to-end
- Loading states, empty states, error handling
- Responsive layout pass
- **Demo:** full vibe query + discovery flow working. Commit + push.

---

### Week 4 — Polish & Deploy

- "Save to Spotify" — `/playlist/create` saves playlist to user's Spotify account
- Full UI/UX pass — consistent styling, loading skeletons, mobile layout
- README written — setup instructions, env vars, how to run locally
- Backend deployed to Render, all env vars configured
- Smoke test every endpoint against Render deployment
- Frontend deployed to Vercel, connected to production backend
- Spotify redirect URI updated to production URL in Developer Portal
- Full end-to-end test on production — login → vibe → playlist → save
- Debug logs and dead code removed
- Tag release on GitHub
- **Final demo on production URL. Project complete.**

---

### Working style

- First block each session: no AI assist — focus on hard logic, reading docs, debugging API responses. Write down specific Cursor tasks for later.
- Second block: Cursor ON for boilerplate, UI, repetitive patterns.
- End of each session: review every AI-written line before committing. Descriptive commit messages.

---

## 10. Open Questions

- ~~Which LLM provider?~~ → Gemini 2.5 Flash (Google AI Studio)
- What exactly are we embedding in ChromaDB? (See Section 6)
- Session storage strategy for tokens — in-memory, cookie, or Redis?
- Do we need a database at all beyond ChromaDB? (e.g. to persist generated playlists)
- Deployment targets confirmed: Vercel (frontend) + Render (backend)?
- TODO: add your own open questions

---

## 11. Resources

- [Spotify Web API Reference](https://developer.spotify.com/documentation/web-api)
- [Spotify Audio Features](https://developer.spotify.com/documentation/web-api/reference/get-audio-features)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Next.js Docs](https://nextjs.org/docs)
- [ChromaDB Docs](https://docs.trychroma.com/)
- TODO: add OAuth tutorial link once you find a good one

