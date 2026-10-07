import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#f2f7ff",
          100: "#e6efff",
          500: "#3b6fed",
          600: "#2f5bd1",
          700: "#2748a6",
        },
      },
    },
  },
  plugins: [],
};

export default config;
