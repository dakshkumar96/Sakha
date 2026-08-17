import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        "bg-deep": "var(--bg-deep)",
        "bg-field": "var(--bg-field)",
        gold: "var(--gold)",
        "gold-soft": "var(--gold-soft)",
        ink: "var(--ink)",
        "ink-dim": "var(--ink-dim)",
        crisis: "var(--crisis)",
      },
      fontFamily: {
        display: ["var(--font-display)", "ui-sans-serif", "system-ui", "sans-serif"],
        body: ["var(--font-body)", "ui-sans-serif", "system-ui", "sans-serif"],
        sakha: ["Maharaja", "var(--font-display)", "ui-serif", "Georgia", "serif"],
      },
      keyframes: {
        "glow-idle": {
          "0%, 100%": { opacity: "0.55", transform: "scale(1)" },
          "50%": { opacity: "0.8", transform: "scale(1.03)" },
        },
        "pulse-listen": {
          "0%, 100%": { opacity: "0.6", transform: "scale(1)" },
          "50%": { opacity: "1", transform: "scale(1.12)" },
        },
        breathe: {
          "0%, 100%": { opacity: "0.4", transform: "scale(0.98)" },
          "50%": { opacity: "0.75", transform: "scale(1.05)" },
        },
        "dust-drift": {
          "0%": { transform: "translateY(0) translateX(0)", opacity: "0" },
          "10%": { opacity: "0.5" },
          "90%": { opacity: "0.3" },
          "100%": { transform: "translateY(-40px) translateX(12px)", opacity: "0" },
        },
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        "glow-idle": "glow-idle 6s ease-in-out infinite",
        "pulse-listen": "pulse-listen 1.8s ease-in-out infinite",
        breathe: "breathe 2.4s ease-in-out infinite",
        "dust-drift": "dust-drift 12s linear infinite",
        "fade-up": "fade-up 0.5s ease-out both",
      },
    },
  },
  plugins: [],
};

export default config;
