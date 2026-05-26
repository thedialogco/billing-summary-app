/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50:  "#e8f4f3",
          100: "#d4e9e7",
          200: "#b3d4d2",
          700: "#0D3B38",
          800: "#0a2e2b",
          900: "#072422",
        },
      },
    },
  },
  plugins: [],
}

