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
            primary: 'rgba(15, 23, 42, 0.9)',    // Very dark blue/gray
            secondary: 'rgba(30, 41, 59, 0.8)',   // Dark blue/gray
            muted: 'rgba(51, 65, 85, 0.7)'       // Medium blue/gray
          }
        }
      },
      backgroundImage: {
        'dream-gradient': 'radial-gradient(circle at top right, rgba(139, 92, 246, 0.02), transparent), radial-gradient(circle at bottom left, rgba(236, 72, 153, 0.02), transparent)'
      }
    }
  },
  plugins: [
    require('@tailwindcss/typography')
  ]
}
