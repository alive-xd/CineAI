/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: "#E50914",
          dark: "#B20710",
          light: "#FF1F2B",
        },

        surface: {
          DEFAULT: "#141414",
          card: "#1C1C1C",
          raised: "#242424",
          overlay: "#2C2C2C",
        },

        text: {
          primary: "#FFFFFF",
          secondary: "#A3A3A3",
          muted: "#737373",
        },

        accent: {
          gold: "#F5C518",
          teal: "#00B4D8",
          purple: "#7C3AED",
          green: "#22C55E",
        },
      },

      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};