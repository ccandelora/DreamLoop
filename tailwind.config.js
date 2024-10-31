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
          accent: '#6366F1',     // Indigo
          text: {
            primary: '#FFFFFF',    // Pure white for maximum contrast
            secondary: '#E5E7EB',  // Lighter gray for better visibility
            muted: '#9CA3AF'      // Brighter muted text
          }
        }
      },
      backgroundImage: {
        'dream-gradient': 'radial-gradient(circle at top right, rgba(139, 92, 246, 0.03), transparent), radial-gradient(circle at bottom left, rgba(236, 72, 153, 0.03), transparent)'
      }
    }
  },
  plugins: [
    require('@tailwindcss/typography')
  ]
}
