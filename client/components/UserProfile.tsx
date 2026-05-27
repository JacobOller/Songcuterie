"use client";

import { useEffect, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

export default function UserProfile() {
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState<unknown>(null);
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

        const data = await res.json();
        setUser(data);
      } catch {
        setError("Could not load profile");
      } finally {
        setLoading(false);
      }
    }

    loadProfile();
  }, []);

  if (loading) return <p>Loading profile...</p>;
  if (error) return <p>{error}</p>;

  return <pre>{JSON.stringify(user, null, 2)}</pre>;
}