/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // ── Deep navy sidebar/header ────────────────────────────────────────
        navy: {
          50:  '#f0f5ff',
          100: '#e0eaff',
          200: '#c4d4f5',
          300: '#93b0e8',
          400: '#5e87d6',
          500: '#3b64c4',
          600: '#2248a8',
          700: '#1a3a8f',
          800: '#152f75',
          900: '#0B1F3A',
          950: '#071429',
        },
        // ── Content-area accent (blue) ────────────────────────────────────
        primary: {
          50:  '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
        },
        // ── App content shell ──────────────────────────────────────────────
        app: {
          bg:     '#F8FAFC',   // main page background — very light blue-gray
          card:   '#FFFFFF',   // white card background
          border: '#E2E8F0',   // border color
          muted:  '#94A3B8',   // muted text
        },
        // ── Dark sidebar palette (kept for sidebar/header) ─────────────────
        surface: {
          DEFAULT: '#0B1F3A',
          800: '#102A4C',
          900: '#0B1F3A',
          950: '#071429',
        },
        // ── Brand accent (kept for compatibility) ──────────────────────────
        brand: {
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
        },
        // ── Saffron for landing CTAs ───────────────────────────────────────
        saffron: {
          400: '#f5a623',
          500: '#e8930a',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'monospace'],
      },
      boxShadow: {
        card:       '0 1px 3px 0 rgba(0,0,0,.08), 0 1px 2px -1px rgba(0,0,0,.04)',
        'card-md':  '0 4px 12px 0 rgba(0,0,0,.10)',
        'card-lg':  '0 8px 24px 0 rgba(0,0,0,.12)',
        'sidebar':  '2px 0 8px 0 rgba(0,0,0,.15)',
      },
    },
  },
  plugins: [],
}
