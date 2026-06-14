import Link from "next/link";
import MoodSearchTest from "@/components/MoodSearchTest";

export default function SearchPage() {
  return (
    <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-8 px-6 py-10">
      <header className="space-y-2">
        <p className="text-sm text-zinc-500 dark:text-zinc-400">Songcuterie</p>
        <h1 className="text-3xl font-semibold tracking-tight">Mood parser test</h1>
        <p className="text-zinc-600 dark:text-zinc-300">
          Type a vibe to parse with Gemini and get ~10 Spotify recommendations. Log in
          with Spotify first (use 127.0.0.1 for both sites).
        </p>
      </header>

      <section className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-800 dark:bg-zinc-950">
        <MoodSearchTest />
      </section>

      <footer className="flex flex-wrap gap-4 text-sm">
        <Link
          href="/discover"
          className="text-zinc-700 underline underline-offset-4 hover:text-zinc-900 dark:text-zinc-300 dark:hover:text-zinc-100"
        >
          Discover
        </Link>
        <Link
          href="/"
          className="text-zinc-700 underline underline-offset-4 hover:text-zinc-900 dark:text-zinc-300 dark:hover:text-zinc-100"
        >
          Back to home
        </Link>
      </footer>
    </main>
  );
}
