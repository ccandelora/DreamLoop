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
          primary: '#8B5CF6',    // Violet
          secondary: '#EC4899',  // Pink
          accent: '#6366F1'      // Indigo
        }
      },
      backgroundImage: {
        'dream-gradient': 'radial-gradient(circle at top right, rgb(139, 92, 246, 0.1), transparent), radial-gradient(circle at bottom left, rgb(236, 72, 153, 0.1), transparent)'
      }
    }
  },
  plugins: [],
  darkMode: 'class'
}
