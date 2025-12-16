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
        // Trading terminal dark theme
        terminal: {
          bg: "#0a0a0f",
          surface: "#12121a",
          elevated: "#1a1a24",
          border: "#2a2a3a",
          muted: "#6b7280",
        },
        // Trading colors
        bull: {
          DEFAULT: "#00d4aa",
          light: "#00ffcc",
          dark: "#00a080",
        },
        bear: {
          DEFAULT: "#ff4757",
          light: "#ff6b7a",
          dark: "#cc3a47",
        },
        // Accent colors
        accent: {
          primary: "#00d4ff",
          secondary: "#8b5cf6",
          tertiary: "#fbbf24",
        },
      },
      fontFamily: {
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
        sans: ["DM Sans", "Inter", "system-ui", "sans-serif"],
        display: ["Unbounded", "DM Sans", "sans-serif"],
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "flash-green": "flash-green 0.3s ease-out",
        "flash-red": "flash-red 0.3s ease-out",
        "slide-up": "slide-up 0.3s ease-out",
        "fade-in": "fade-in 0.2s ease-out",
      },
      keyframes: {
        "flash-green": {
          "0%": { backgroundColor: "rgba(0, 212, 170, 0.3)" },
          "100%": { backgroundColor: "transparent" },
        },
        "flash-red": {
          "0%": { backgroundColor: "rgba(255, 71, 87, 0.3)" },
          "100%": { backgroundColor: "transparent" },
        },
        "slide-up": {
          "0%": { transform: "translateY(10px)", opacity: "0" },
          "100%": { transform: "translateY(0)", opacity: "1" },
        },
        "fade-in": {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
      },
    },
  },
  plugins: [],
};
export default config;

