/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        night: {
          950: "#0B1420",
          900: "#0F1B2D",
          800: "#16243B",
          700: "#1E304C",
          600: "#2C4368",
        },
        signal: {
          DEFAULT: "#F2A65A",
          soft: "#F7C68A",
          deep: "#D98A3D",
        },
        pulse: {
          DEFAULT: "#4FD1C5",
          soft: "#8FE3DA",
        },
        mist: {
          100: "#F5F3EE",
          300: "#D9DFEA",
          500: "#93A1B8",
          700: "#5A6B85",
        },
      },
      fontFamily: {
        display: ["'Space Grotesk'", "sans-serif"],
        body: ["'Inter'", "sans-serif"],
      },
    },
  },
  plugins: [],
};
