/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{html,js}"],
  darkMode: true,
  theme: {
    extend: {
      colors: {
        background: "#fafafa",
        primary: "#1F70B9", // just gonna borrow this @intellitect... it's a good blue!
        text: {
          DEFAULT: "#2d3441",
        },
        dark: "#242934",
      },
    },
  },
  plugins: [],
};
