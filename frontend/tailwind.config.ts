import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        "goat-black":   "#08080f",
        "goat-surface": "#0D0D1A",
        "goat-card":    "#1A1A2E",
        "goat-border":  "#2A2A4A",
        "goat-purple":  "#6100ff",
        "goat-button":  "#7c3aed",
        "goat-violet":  "#8B5CF6",
        "goat-green":   "#53c660",
        "goat-amber":   "#f59e0b",
        "goat-cheese":  "#22c55e",
        "goat-red":     "#ef4444",
        "goat-white":   "#F5F5F5",
        "goat-silver":  "#C0C0C0",
      },
      fontFamily: {
        syne:    ["var(--font-syne-var)", "Syne", "sans-serif"],
        "dm-sans": ["var(--font-dm-sans-var)", "DM Sans", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
