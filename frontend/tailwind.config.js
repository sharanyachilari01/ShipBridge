/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          dark: '#0f172a',      // Slate 900 (Navy/Charcoal text)
          card: '#ffffff',      // Pure White Card
          bg: '#f8fafc',        // Off-white / Light Gray Background
          primary: '#2563eb',   // Blue for normal active states
          warning: '#f59e0b',   // Amber for warning
          critical: '#e11d48',  // Red ONLY for misplaced/critical states
          success: '#059669',   // Green for successful/on-track states
        }
      }
    },
  },
  plugins: [],
}
