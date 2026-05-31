/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        background: '#0f1117',
        surface: '#1a1d27',
        elevated: '#252836',
        accent: '#4f8cff',
        'accent-dim': '#2a5bcc',
        'text-primary': '#e4e6ed',
        'text-secondary': '#8b8fa3',
        border: '#2e3144',
        success: '#22c55e',
        warning: '#f59e0b',
        error: '#ef4444',
      },
    },
  },
  plugins: [require('tailwindcss-animate'), require('@tailwindcss/typography')],
}
