/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      colors: {
        vault: {
          bg: "#020817",
          panel: "#0f172a",
          border: "#1e293b",
          text: "#e2e8f0",
          muted: "#64748b",
          accent: "#38bdf8",
          danger: "#ef4444",
          success: "#22c55e",
          warning: "#f59e0b",
        },
      },
    },
  },
  plugins: [],
};
