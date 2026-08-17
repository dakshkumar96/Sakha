import type { Metadata, Viewport } from "next";
import { DM_Sans, EB_Garamond } from "next/font/google";
import "./globals.css";

// Krishna's voice: verse citations, the onboarding threshold line — text
// serif with real weight at body size, not a display face. UI chrome (nav
// labels, sidebar headers, dialogs) stays on font-body/DM Sans, never this.
const display = EB_Garamond({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-display",
  display: "swap",
});

const body = DM_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-body",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Sakha — a companion with the Gita",
  description:
    "A reflective companion grounded in the Bhagavad Gita. Speak or type; every teaching cites chapter and verse.",
};

export const viewport: Viewport = {
  themeColor: "#050d1a",
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${display.variable} ${body.variable}`}>
      <body>{children}</body>
    </html>
  );
}
