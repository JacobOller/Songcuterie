import Link from "next/link";
import DiscoverySearch from "@/components/DiscoverySearch";

export default function DiscoverPage() {
  return (
    <main className="mx-auto flex w-full max-w-2xl flex-1 flex-col gap-8 px-6 py-10">
      <header className="space-y-2">
        <p className="text-sm font-medium tracking-wide text-zinc-500 dark:text-zinc-400">
          CurateFM
        </p>
        <h1 className="text-3xl font-semibold tracking-tight">Discover</h1>
        <p className="text-zinc-600 dark:text-zinc-300">
          Find songs that match your vibe — scored by how well they fit you, not bundled into
          a playlist. Log in with Spotify first.
        </p>
      </header>

      <section className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-800 dark:bg-zinc-950">
        <DiscoverySearch />
      </section>

      <footer className="flex flex-wrap gap-4 text-sm">
        <Link
          href="/search"
          className="text-zinc-700 underline underline-offset-4 hover:text-zinc-900 dark:text-zinc-300 dark:hover:text-zinc-100"
        >
          Mood search
        </Link>
        <Link
          href="/profile"
          className="text-zinc-700 underline underline-offset-4 hover:text-zinc-900 dark:text-zinc-300 dark:hover:text-zinc-100"
        >
          Profile
        </Link>
        <Link
          href="/"
          className="text-zinc-700 underline underline-offset-4 hover:text-zinc-900 dark:text-zinc-300 dark:hover:text-zinc-100"
        >
          Home
        </Link>
      </footer>
    </main>
  );
}
