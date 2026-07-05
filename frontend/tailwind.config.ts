import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: "#0d0e10",
        panel: "#15171a",
        panel2: "#1b1e22",
        line: "#262a30",
        line2: "#39414a",
        fg: "#e7e8ea",
        muted: "#9aa1a9",
        faint: "#6b727b",
        ok: "#3ddc97",
        warn: "#e0a83e",
        bad: "#e06c5b",
        accent: "#3ddc97",
      },
      fontFamily: {
        mono: ["ui-monospace", "SF Mono", "JetBrains Mono", "Menlo", "monospace"],
        sans: ["-apple-system", "BlinkMacSystemFont", "Inter", "Segoe UI", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
