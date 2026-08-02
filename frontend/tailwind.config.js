/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: {
          50: "#eff6ff",
          100: "#dbeafe",
          500: "#3b82f6",
          600: "#2563eb",
          700: "#1d4ed8",
        },
        success: { 100: "#dcfce7", 600: "#16a34a", 700: "#15803d" },
        warning: { 100: "#fef3c7", 600: "#d97706", 700: "#b45309" },
        danger: { 100: "#fee2e2", 600: "#dc2626", 700: "#b91c1c" },
        info: { 100: "#e0f2fe", 600: "#0284c7", 700: "#0369a1" },
      },
      spacing: {
        4.5: "1.125rem",
      },
    },
  },
  plugins: [],
};
