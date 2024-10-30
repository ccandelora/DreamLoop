/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
    './static/**/*.{js,css}'
  ],
  theme: {
    extend: {
      colors: {
        dream: {
          primary: 'rgba(138, 43, 226, 0.7)',
          secondary: 'rgba(70, 130, 180, 0.7)',
          accent: 'rgba(147, 112, 219, 0.4)'
        }
      },
      backgroundImage: {
        'dream-gradient': 'radial-gradient(circle at top right, rgba(138, 43, 226, 0.1), transparent), radial-gradient(circle at bottom left, rgba(70, 130, 180, 0.1), transparent)'
      }
    }
  },
  plugins: [],
  darkMode: 'class'
}
