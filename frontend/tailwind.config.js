/** @type {import('tailwindcss').Config} */
const tokens = require('./src/design-tokens.json');

module.exports = {
    content: [
        "./src/**/*.{html,ts}",
    ],
    theme: {
        extend: {
            colors: {
                ...tokens.colors,
                // Compatibility mapping for legacy primary usage
                // primary: { ... } - REMOVED to enforce SSOT using design-tokens.json
            },
            keyframes: {
                'indeterminate-bar': {
                    '0%': { transform: 'translateX(-100%) scaleX(0.2)' },
                    '50%': { transform: 'translateX(0%) scaleX(0.5)' },
                    '100%': { transform: 'translateX(100%) scaleX(0.2)' }
                },
                'fade-in': {
                    '0%': { opacity: '0' },
                    '100%': { opacity: '1' }
                },
                'slide-up': {
                    '0%': { transform: 'translateY(20px)', opacity: '0' },
                    '100%': { transform: 'translateY(0)', opacity: '1' }
                },
                'slide-in-right': {
                    '0%': { transform: 'translateX(100%)' },
                    '100%': { transform: 'translateX(0)' }
                }
            },
            animation: {
                'indeterminate-bar': 'indeterminate-bar 1.5s infinite linear',
                'fade-in': 'fade-in 0.3s ease-out',
                'slide-up': 'slide-up 0.4s ease-out',
                'slide-in-right': 'slide-in-right 0.3s ease-out'
            }
        },
    },
    plugins: [
        require('@tailwindcss/typography'),
    ],
}
