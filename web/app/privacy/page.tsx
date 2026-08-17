import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Privacy — Sakha",
  description: "What Sakha does and does not collect.",
};

export default function PrivacyPage() {
  return (
    <main className="dusk-field min-h-[100dvh] px-5 py-10 md:px-8 md:py-14">
      <div className="mx-auto w-full max-w-[36rem]">
        <Link
          href="/"
          className="onboard-accent font-sakha text-[1.15rem] font-bold tracking-[0.06em] transition-opacity hover:opacity-90"
        >
          Sakha
        </Link>

        <h1 className="mt-8 font-display text-[2rem] font-medium tracking-wide text-ink md:text-[2.25rem]">
          Privacy
        </h1>

        <div className="mt-8 space-y-5 font-body text-[1.02rem] leading-[1.75] text-ink-dim">
          <p>No sign-in is required.</p>
          <p>No personal information is collected or stored.</p>
          <p>
            Words are used only to shape a reply in the moment. Conversations
            are not saved to a database.
          </p>
          <p>
            There is no analytics, no tracking, and no sharing with third
            parties for ads or data sales.
          </p>
          <p>
            Voice input stays in the browser. Recordings are not kept.
          </p>
          <p>This is a personal project with no commercial intent.</p>
        </div>

        <p className="mt-12 font-body text-[0.8rem] text-ink-dim">
          <Link href="/about" className="underline-offset-4 hover:text-gold hover:underline">
            About
          </Link>
        </p>
      </div>
    </main>
  );
}
