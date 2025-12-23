module.exports = {
  content: [
    "./templates/**/*.html",
    "./static/js/**/*.js"
  ],
  safelist: [
    'btn-primary',
    'badge-already',
    'kiosk-left--premium',
    'kiosk-top--premium',
    'pill-btn',
    'btn-muted'
  ],
  theme: {
    extend: {
      keyframes: {
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
      animation: {
        slideUp: 'slideUp 0.4s ease-out',
      }
    },
  },
  plugins: [],
};
