"use client";

import Image from "next/image";
import { useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

type DiscoverTrack = {
  id: string;
  name: string;
  artists: { name: string }[];
  album?: { name: string; images?: { url: string }[] };
  similarity: number;
  reason?: string;
};

type DiscoverResponse = {
  tracks: DiscoverTrack[];
};

function similarityColor(score: number): string {
  if (score >= 8) return "text-green-700 dark:text-green-400";
  if (score >= 5) return "text-amber-700 dark:text-amber-400";
  return "text-zinc-500 dark:text-zinc-400";
}

function SimilarityBadge({ score }: { score: number }) {
  const clamped = Math.min(10, Math.max(1, Math.round(score)));
  return (
    <div className="flex shrink-0 flex-col items-center gap-0.5">
      <span
        className={`text-2xl font-semibold tabular-nums leading-none ${similarityColor(clamped)}`}
      >
        {clamped}
      </span>
      <span className="text-[10px] font-medium uppercase tracking-wide text-zinc-400">
        / 10
      </span>
    </div>
  );
}

function TrackRow({ track }: { track: DiscoverTrack }) {
  const imageUrl = track.album?.images?.[0]?.url;
  const artistNames = track.artists.map((a) => a.name).join(", ");

  return (
    <li className="flex items-center gap-4 border-b border-zinc-100 px-4 py-3 last:border-b-0 dark:border-zinc-800">
      <div className="relative h-12 w-12 shrink-0 overflow-hidden rounded-md bg-zinc-200 dark:bg-zinc-800">
        {imageUrl ? (
          <Image
            src={imageUrl}
            alt={track.album?.name ?? track.name}
            fill
            sizes="48px"
            className="object-cover"
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center text-xs text-zinc-400">
            ♪
          </div>
        )}
      </div>

      <div className="min-w-0 flex-1">
        <p className="truncate font-medium text-zinc-900 dark:text-zinc-100">
          {track.name}
        </p>
        <p className="truncate text-sm text-zinc-600 dark:text-zinc-400">{artistNames}</p>
        {track.reason && (
          <p className="mt-1 line-clamp-2 text-xs text-zinc-500 dark:text-zinc-500">
            {track.reason}
          </p>
        )}
      </div>

      <SimilarityBadge score={track.similarity} />
    </li>
  );
}

export default function DiscoverySearch() {
  const [vibe, setVibe] = useState("");
  const [similarTo, setSimilarTo] = useState("");
  const [newness, setNewness] = useState(3);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tracks, setTracks] = useState<DiscoverTrack[]>([]);
  const [hasSearched, setHasSearched] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmedVibe = vibe.trim();
    if (!trimmedVibe) return;

    setLoading(true);
    setError(null);
    setTracks([]);
    setHasSearched(true);

    try {
      const res = await fetch(`${API_URL}/search/discover`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          vibe: trimmedVibe,
          similar_to: similarTo.trim() || undefined,
          newness,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        setError(typeof data.detail === "string" ? data.detail : "Request failed");
        return;
      }

      const result = data as DiscoverResponse;
      setTracks(result.tracks ?? []);
    } catch {
      setError("Could not reach the API. Is the backend running on :8000?");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-8">
      <form onSubmit={handleSubmit} className="space-y-6">
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

        <label className="block space-y-2">
          <span className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
            Similar to{" "}
            <span className="font-normal text-zinc-500 dark:text-zinc-400">(optional)</span>
          </span>
          <input
            type="text"
            value={similarTo}
            onChange={(e) => setSimilarTo(e.target.value)}
            placeholder="e.g. Men I Trust, Khruangbin"
            maxLength={200}
            className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-zinc-900 placeholder:text-zinc-400 focus:border-zinc-500 focus:outline-none dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100"
          />
        </label>

        <div className="space-y-3">
          <div className="flex items-center justify-between text-sm">
            <span className="font-medium text-zinc-700 dark:text-zinc-300">Newness</span>
            <span className="font-mono text-zinc-500 dark:text-zinc-400">{newness}</span>
          </div>
          <input
            type="range"
            min={1}
            max={5}
            step={1}
            value={newness}
            onChange={(e) => setNewness(Number(e.target.value))}
            className="h-2 w-full cursor-pointer accent-zinc-900 dark:accent-zinc-100"
          />
          <div className="flex justify-between text-xs text-zinc-500 dark:text-zinc-400">
            <span>Not very new</span>
            <span>Very new</span>
          </div>
        </div>

        <button
          type="submit"
          disabled={loading || !vibe.trim()}
          className="w-full rounded-lg bg-zinc-900 px-4 py-2.5 text-sm font-medium text-white disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900 sm:w-auto"
        >
          {loading ? "Discovering…" : "Discover"}
        </button>
      </form>

      {error && (
        <p className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800 dark:border-red-900 dark:bg-red-950 dark:text-red-200">
          {error}
        </p>
      )}

      <section className="space-y-3">
        <div className="flex items-baseline justify-between gap-4">
          <h2 className="text-lg font-medium">Results</h2>
          {tracks.length > 0 && (
            <span className="text-sm text-zinc-500 dark:text-zinc-400">
              {tracks.length} {tracks.length === 1 ? "song" : "songs"}
            </span>
          )}
        </div>

        {!hasSearched && (
          <p className="rounded-lg border border-dashed border-zinc-200 px-4 py-8 text-center text-sm text-zinc-500 dark:border-zinc-800 dark:text-zinc-400">
            Describe a vibe and hit Discover to see matching songs with similarity scores.
          </p>
        )}

        {hasSearched && !loading && !error && tracks.length === 0 && (
          <p className="rounded-lg border border-zinc-200 px-4 py-8 text-center text-sm text-zinc-500 dark:border-zinc-800 dark:text-zinc-400">
            No songs matched your search. Try adjusting the vibe or newness slider.
          </p>
        )}

        {tracks.length > 0 && (
          <div className="overflow-hidden rounded-xl border border-zinc-200 dark:border-zinc-800">
            <ul className="max-h-[28rem] overflow-y-auto">
              {tracks.map((track) => (
                <TrackRow key={track.id} track={track} />
              ))}
            </ul>
          </div>
        )}
      </section>
    </div>
  );
}
