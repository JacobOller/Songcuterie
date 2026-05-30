import Link from "next/link";
import TopTracks from "@/components/TopTracks";
import UserProfile from "@/components/UserProfile";

export default function ProfilePage() {
  return (
    <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-8 px-6 py-10">
      <header className="space-y-2">
        <p className="text-sm text-zinc-500 dark:text-zinc-400">Songcuterie</p>
        <h1 className="text-3xl font-semibold tracking-tight">Spotify Profile</h1>
        <p className="text-zinc-600 dark:text-zinc-300">
          Your authenticated Spotify account details.
        </p>
      </header>

      <section className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-800 dark:bg-zinc-950">
        <h2 className="mb-4 text-lg font-medium">Profile</h2>
        <UserProfile />
      </section>

      <section className="rounded-xl border border-zinc-200 bg-white p-5 shadow-sm dark:border-zinc-800 dark:bg-zinc-950">
        <h2 className="mb-4 text-lg font-medium">Top Tracks</h2>
        <TopTracks />
      </section>

      <footer>
        <Link
          href="/"
          className="text-sm text-zinc-700 underline underline-offset-4 hover:text-zinc-900 dark:text-zinc-300 dark:hover:text-zinc-100"
        >
          Back to home
        </Link>
      </footer>
    </main>
  );
}
