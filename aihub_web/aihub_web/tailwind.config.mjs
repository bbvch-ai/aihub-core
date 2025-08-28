import animate from 'tailwindcss-animate'
import primevue from 'tailwindcss-primeui'

/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ['class'],
  safelist: ['dark'],
  prefix: '',

  theme: {
    container: {
      center: true,
      padding: '2rem',
      screens: {
        '2xl': '1400px',
      },
    },
    extend: {
      colors: {
        surface: {
          850: 'var(--p-surface-850)',
        },
      },
    },
  },
  plugins: [animate, primevue],
}
