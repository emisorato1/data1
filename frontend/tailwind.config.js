/** @type {import('tailwindcss').Config} */
module.exports = {
    darkMode: ["class"],
    content: [
        "./src/**/*.{ts,tsx}",
    ],
    theme: {
        container: {
            center: true,
            padding: "2rem", // We'll override this with custom utilities
        },
        screens: {
            sm: "576px",
            md: "768px",
            lg: "960px",
            xl: "1200px",
            xxl: "1400px",
        },
        extend: {
            fontFamily: {
                sans: ['var(--font-dm-sans)', 'Public Sans', 'Roboto', 'sans-serif'],
            },
            fontSize: {
                'display-lg': ['48px', { lineHeight: '60px' }],
                'display-md': ['36px', { lineHeight: '48px' }],
                'display-sm': ['32px', { lineHeight: '40px' }],

                'heading-xl': ['28px', { lineHeight: '40px' }],
                'heading-lg': ['24px', { lineHeight: '32px' }],
                'heading-md': ['20px', { lineHeight: '30px' }],
                'heading-sm': ['18px', { lineHeight: '28px' }],

                'body-lg': ['18px', { lineHeight: '24px' }],
                'body-md': ['16px', { lineHeight: '20px' }],
                'body-sm': ['14px', { lineHeight: '20px' }],

                'caption': ['12px', { lineHeight: '20px' }],
            },
            colors: {
                border: "hsl(var(--border))",
                input: "hsl(var(--input))",
                ring: "hsl(var(--ring))",
                background: "hsl(var(--background))",
                foreground: "hsl(var(--foreground))",
                neutral: {
                    50: "#FEFEFE",
                    100: "#F8FAFA",
                    400: "#C4C7C7",
                },
                primary: {
                    DEFAULT: "hsl(var(--primary))",
                    foreground: "hsl(var(--primary-foreground))",
                },
                secondary: {
                    DEFAULT: "hsl(var(--secondary))",
                    foreground: "hsl(var(--secondary-foreground))",
                },
                destructive: {
                    DEFAULT: "hsl(var(--destructive))",
                    foreground: "hsl(var(--destructive-foreground))",
                },
                muted: {
                    DEFAULT: "hsl(var(--muted))",
                    foreground: "hsl(var(--muted-foreground))",
                },
                accent: {
                    DEFAULT: "hsl(var(--accent))",
                    foreground: "hsl(var(--accent-foreground))",
                },
                popover: {
                    DEFAULT: "hsl(var(--popover))",
                    foreground: "hsl(var(--popover-foreground))",
                },
                card: {
                    DEFAULT: "hsl(var(--card))",
                    foreground: "hsl(var(--card-foreground))",
                },
                sidebar: {
                    DEFAULT: "hsl(var(--sidebar-bg))",
                    border: "hsl(var(--sidebar-border))",
                },
                /* Brand Banco Macro — mapped from CSS vars in globals.css */
                brand: {
                    DEFAULT: "hsl(var(--brand-primary))",
                    dark: "hsl(var(--brand-primary-dark))",
                    light: "hsl(var(--brand-primary-light))",
                    text: "hsl(var(--brand-text))",
                    bg: "hsl(var(--brand-bg))",
                    bg2: "hsl(var(--brand-bg-2))",
                    accent: "hsl(var(--brand-accent))",
                },
                "brand-individuos": "hsl(var(--brand-individuos))",
                "brand-agro": "hsl(var(--brand-agro))",
            },
            borderRadius: {
                none: "0px",
                xs: "4px", // Autocomplete, Snackbars, Text fields
                sm: "8px", // Chips, Cards small
                md: "12px", // Banner, Fab
                lg: "16px", // Bottom sheets, Dialogs
                full: "100px", // Buttons, Badges, Sliders
                // Fallbacks para las demas variables si hacian uso de radius:
                DEFAULT: "12px",
            },
            borderWidth: {
                1: "1px",
                2: "2px",
                3: "3px",
                4: "4px",
            },
            boxShadow: {
                'lvl-1': '0px 2px 8px -2px rgba(46, 49, 50, 0.3)',
                'lvl-2': '0px 4px 20px -8px rgba(46, 49, 50, 0.4)',
                'lvl-3': '0px 4px 16px 4px rgba(46, 49, 50, 0.1)',
                'lvl-4': '0px 8px 20px -10px rgba(46, 49, 50, 0.12), 0px 4px 30px 4px rgba(46, 49, 50, 0.12)',
                'lvl-5': '0px 2px 14px 2px rgba(46, 49, 50, 0.24), 0px 2px 14px 2px rgba(46, 49, 50, 0.24)',
            },
            spacing: {
                // To ensure multiples of 4 and 8 are explicitly available
                // Tailwind default already has multiples of 4px up to 96
            },
            keyframes: {
                "accordion-down": {
                    from: { height: 0 },
                    to: { height: "var(--radix-accordion-content-height)" },
                },
                "accordion-up": {
                    from: { height: "var(--radix-accordion-content-height)" },
                    to: { height: 0 },
                },
            },
            animation: {
                "accordion-down": "accordion-down 0.2s ease-out",
                "accordion-up": "accordion-up 0.2s ease-out",
            },
        },
    },
    plugins: [
        require("tailwindcss-animate"),
        require("@tailwindcss/typography"),
    ],
}
