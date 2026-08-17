import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "About — Sakha",
  description: "Why Sakha exists, in plain words.",
};

export default function AboutPage() {
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
          About
        </h1>

        <div className="mt-8 space-y-5 font-body text-[1.02rem] leading-[1.75] text-ink-dim">
          <p>
            Sakha exists because the Bhagavad Gita still speaks to people who
            are stuck, afraid, or carrying something they cannot name. It is a
            place to say what is heavy, meet real questions first, then receive
            a teaching that points back to an actual chapter and verse.
          </p>
          <p>
            Sakha means friend in Sanskrit. Krishna calls Arjuna his sakha. The
            name is for that bond, not a claim to divinity.
          </p>
          <p>
            This is a personal project. Not a company. Not a product launch.
            Built with care for what the text actually says.
          </p>
          <p className="text-ink/90">
            For anyone who wants honest company with the Gita when the night is
            long and the answers feel thin.
          </p>
        </div>

        <p className="mt-12 font-body text-[0.8rem] text-ink-dim">
          <Link href="/privacy" className="underline-offset-4 hover:text-gold hover:underline">
            Privacy
          </Link>
        </p>
      </div>
    </main>
  );
}
