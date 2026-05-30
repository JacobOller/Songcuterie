"use client";

import { useEffect, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

type SpotifyArtist = { name: string };
type SpotifyTrack = {
  name: string;
  artists: SpotifyArtist[];
};
type TopTracksResponse = {
  items?: SpotifyTrack[];
};

export default function TopTracks() {
  const [loading, setLoading] = useState(true);
  const [tracks, setTracks] = useState<SpotifyTrack[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadTopTracks() {
      try {
        const res = await fetch(`${API_URL}/user/top-tracks`, {
          credentials: "include",
          cache: "no-store",
        });

        if (!res.ok) {
          setError("Could not load top tracks");
          return;
        }

        const data: TopTracksResponse = await res.json();
        setTracks(data.items ?? []);
      } catch {
        setError("Could not load top tracks");
      } finally {
        setLoading(false);
      }
    }

    loadTopTracks();
  }, []);

  if (loading) return <p>Loading top tracks...</p>;
  if (error) return <p>{error}</p>;
  if (tracks.length === 0) return <p>No top tracks found.</p>;

  return (
    <ol className="list-decimal space-y-2 pl-5">
      {tracks.map((track, index) => (
        <li key={`${track.name}-${index}`}>
          <span className="font-medium">{track.name}</span>
          {" — "}
          <span className="text-zinc-600 dark:text-zinc-300">
            {track.artists.map((artist) => artist.name).join(", ")}
          </span>
        </li>
      ))}
    </ol>
  );
}
