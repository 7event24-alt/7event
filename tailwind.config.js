module.exports = {
  content: [
    './base/templates/**/*.html',
    './base/**/templates/**/*.html',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#1e3a5f',
          dark: '#152a45',
          light: '#2d4a6f',
        },
        gold: {
          DEFAULT: '#c9a227',
          light: '#dbb942',
          dark: '#a8871f',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}