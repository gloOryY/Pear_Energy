import type { Config } from 'tailwindcss';

const config: Config = {
  darkMode: ['class'],
  content: ['./src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        graphite: { 950: '#0e1013', 900: '#14161a', 850: '#191c21', 800: '#1e2228', 750: '#252a31', 700: '#2d333b', 600: '#3a414b' },
        accent: { DEFAULT: '#17c99e', bright: '#2ee6b8', dim: '#0f8f70' },
        danger: '#ef4444',
        warn: '#f59e0b',
        ok: '#22c55e',
      },
      fontFamily: { sans: ['Inter', 'system-ui', 'sans-serif'] },
    },
  },
  plugins: [],
};
export default config;
