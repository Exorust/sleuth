/** Design tokens pulled from the approved design doc.
 *  Dark-first, mono-forward, single orange accent. Light mode deferred to v0.2.
 */
export default {
  content: ["./src/**/*.{astro,html,ts,tsx,md}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        bg: "#0b0d10",
        surface: "#12151a",
        surface2: "#1a1e25",
        fg: "#e7e9ee",
        muted: "#6b7280",
        border: "#262a31",
        accent: "#ff6b3d",
        ok: "#4ade80",
        warn: "#fbbf24",
        err: "#f87171",
        // per-tool colors for trajectory badges
        tool: {
          schema: "#60a5fa",
          top_errors: "#f87171",
          search: "#a78bfa",
          around: "#fbbf24",
          trace: "#34d399",
          submit: "#ff6b3d",
        },
      },
      fontFamily: {
        mono: ["JetBrains Mono", "ui-monospace", "SFMono-Regular", "monospace"],
        sans: ["Inter Tight", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      fontSize: {
        // mono-forward scale
        xs: ["0.75rem", { lineHeight: "1.1rem" }],
        sm: ["0.8125rem", { lineHeight: "1.2rem" }],
        base: ["0.875rem", { lineHeight: "1.35rem" }],
      },
    },
  },
};
