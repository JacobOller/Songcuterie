"use client";

import { useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

type ParsedParams = {
  valence?: number;
  energy?: number;
  acousticness?: number;
  danceability?: number;
  instrumentalness?: number;
  tempo?: number;
  target_genres?: string[];
};

type SpotifyTrack = {
  name: string;
  artists: { name: string }[];
  album?: { name: string; images?: { url: string }[] };
};

type MoodResponse = {
  raw_text: string;
  parsed_params: ParsedParams;
  tracks?: SpotifyTrack[];
  track_source?: string;
};

const FEATURES: { key: keyof ParsedParams; label: string }[] = [
  { key: "valence", label: "Valence" },
  { key: "energy", label: "Energy" },
  { key: "acousticness", label: "Acousticness" },
  { key: "danceability", label: "Danceability" },
  { key: "instrumentalness", label: "Instrumentalness" },
];

export default function MoodSearchTest() {
  const [vibe, setVibe] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<MoodResponse | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = vibe.trim();
    if (!trimmed) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await fetch(`${API_URL}/search/mood`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ raw_text: trimmed }),
      });

      const data = await res.json();

      if (!res.ok) {
        setError(typeof data.detail === "string" ? data.detail : "Request failed");
        return;
      }

      setResult(data);
    } catch {
      setError("Could not reach the API. Is the backend running on :8000?");
    } finally {
      setLoading(false);
    }
  }

  const params = result?.parsed_params;

  return (
    <div className="space-y-6">
      <form onSubmit={handleSubmit} className="space-y-4">
        <label className="block space-y-2">
          <span className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
            Describe a vibe
          </span>
          <textarea
            value={vibe}
            onChange={(e) => setVibe(e.target.value)}
            placeholder="e.g. late night drive in the rain"
            rows={3}
            maxLength={500}
            className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-zinc-900 placeholder:text-zinc-400 focus:border-zinc-500 focus:outline-none dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100"
          />
        </label>
        <button
          type="submit"
          disabled={loading || !vibe.trim()}
          className="rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900"
        >
          {loading ? "Searching…" : "Search mood"}
        </button>
      </form>

      {error && (
        <p className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800 dark:border-red-900 dark:bg-red-950 dark:text-red-200">
          {error}
        </p>
      )}

      {params && (
        <div className="space-y-6">
          <section className="space-y-3">
            <h3 className="text-sm font-medium text-zinc-500 dark:text-zinc-400">
              Audio features
            </h3>
            <dl className="space-y-3">
              {FEATURES.map(({ key, label }) => {
                const value = params[key];
                if (typeof value !== "number") return null;
                return (
                  <div key={key}>
                    <div className="mb-1 flex justify-between text-sm">
                      <dt>{label}</dt>
                      <dd className="font-mono text-zinc-600 dark:text-zinc-400">
                        {value.toFixed(2)}
                      </dd>
                    </div>
                    <div className="h-2 overflow-hidden rounded-full bg-zinc-200 dark:bg-zinc-800">
                      <div
                        className="h-full rounded-full bg-green-600 dark:bg-green-500"
                        style={{ width: `${Math.min(100, value * 100)}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </dl>
          </section>

          {typeof params.tempo === "number" && (
            <section>
              <h3 className="mb-1 text-sm font-medium text-zinc-500 dark:text-zinc-400">
                Tempo
              </h3>
              <p className="text-2xl font-semibold">{Math.round(params.tempo)} BPM</p>
            </section>
          )}

          {params.target_genres && params.target_genres.length > 0 && (
            <section>
              <h3 className="mb-2 text-sm font-medium text-zinc-500 dark:text-zinc-400">
                Target genres
              </h3>
              <div className="flex flex-wrap gap-2">
                {params.target_genres.map((genre) => (
                  <span
                    key={genre}
                    className="rounded-full bg-zinc-100 px-3 py-1 text-sm font-medium text-zinc-800 dark:bg-zinc-800 dark:text-zinc-200"
                  >
                    {genre}
                  </span>
                ))}
              </div>
            </section>
          )}

          {result.tracks && result.tracks.length > 0 && (
            <section>
              <h3 className="mb-3 text-sm font-medium text-zinc-500 dark:text-zinc-400">
                Tracks ({result.tracks.length}
                {result.track_source ? ` · via ${result.track_source}` : ""})
              </h3>
              <ol className="list-decimal space-y-2 pl-5">
                {result.tracks.map((track, index) => (
                  <li key={`${track.name}-${index}`}>
                    <span className="font-medium">{track.name}</span>
                    {" — "}
                    <span className="text-zinc-600 dark:text-zinc-300">
                      {track.artists.map((a) => a.name).join(", ")}
                    </span>
                  </li>
                ))}
              </ol>
            </section>
          )}

          <section>
            <h3 className="mb-2 text-sm font-medium text-zinc-500 dark:text-zinc-400">
              Raw JSON
            </h3>
            <pre className="overflow-x-auto rounded-lg bg-zinc-100 p-4 text-xs text-zinc-800 dark:bg-zinc-900 dark:text-zinc-200">
              {JSON.stringify(result, null, 2)}
            </pre>
          </section>
        </div>
      )}
    </div>
  );
}
