"use client";

import Image from "next/image";
import { useEffect, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

type SpotifyProfile = {
  display_name: string | null;
  email: string | null;
  country: string | null;
  product: string | null;
  followers: { total: number };
  external_urls?: { spotify?: string };
  images: { url: string; height: number | null; width: number | null }[];
};

export default function UserProfile() {
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState<SpotifyProfile | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadProfile() {
      try {
        const res = await fetch(`${API_URL}/auth/me`, {
          credentials: "include",
          cache: "no-store",
        });

        if (!res.ok) {
          setError("Not logged in");
          return;
        }

        const data: SpotifyProfile = await res.json();
        setUser(data);
      } catch {
        setError("Could not load profile");
      } finally {
        setLoading(false);
      }
    }

    loadProfile();
  }, []);

  if (loading) return <p className="text-zinc-500">Loading profile...</p>;
  if (error) return <p className="text-zinc-600 dark:text-zinc-300">{error}</p>;
  if (!user) return null;

  const avatarUrl = user.images[0]?.url;
  const spotifyUrl = user.external_urls?.spotify;

  return (
    <div className="flex flex-col gap-6 sm:flex-row sm:items-start">
      <div className="shrink-0">
        {avatarUrl ? (
          <Image
            src={avatarUrl}
            alt={user.display_name ?? "Profile"}
            width={120}
            height={120}
            className="rounded-full object-cover"
          />
        ) : (
          <div className="flex h-[120px] w-[120px] items-center justify-center rounded-full bg-zinc-200 text-3xl font-semibold text-zinc-500 dark:bg-zinc-800">
            {(user.display_name ?? "?")[0]}
          </div>
        )}
      </div>

      <div className="min-w-0 flex-1 space-y-4">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight">
            {user.display_name ?? "Spotify User"}
          </h2>
          {user.email && (
            <p className="mt-1 text-zinc-600 dark:text-zinc-400">{user.email}</p>
          )}
        </div>

        <dl className="grid grid-cols-2 gap-x-4 gap-y-3 text-sm sm:grid-cols-3">
          <div>
            <dt className="text-zinc-500 dark:text-zinc-400">Country</dt>
            <dd className="font-medium">{user.country ?? "—"}</dd>
          </div>
          <div>
            <dt className="text-zinc-500 dark:text-zinc-400">Plan</dt>
            <dd className="font-medium capitalize">{user.product ?? "—"}</dd>
          </div>
          <div>
            <dt className="text-zinc-500 dark:text-zinc-400">Followers</dt>
            <dd className="font-medium">{user.followers.total}</dd>
          </div>
        </dl>

        {spotifyUrl && (
          <a
            href={spotifyUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-block text-sm font-medium text-green-700 underline underline-offset-4 hover:text-green-800 dark:text-green-400 dark:hover:text-green-300"
          >
            Open Spotify profile
          </a>
        )}
      </div>
    </div>
  );
}
