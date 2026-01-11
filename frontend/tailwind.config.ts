import type { Config } from "tailwindcss";

const config: Config = {
	content: [
		"./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
		"./src/components/**/*.{js,ts,jsx,tsx,mdx}",
		"./src/app/**/*.{js,ts,jsx,tsx,mdx}",
	],
	theme: {
		extend: {
			colors: {
				// Dynamic colors from CSS variables
				background: {
					DEFAULT: "var(--color-bg-primary)",
					secondary: "var(--color-bg-secondary)",
				},
				foreground: {
					DEFAULT: "var(--color-text-primary)",
					secondary: "var(--color-text-secondary)",
					muted: "var(--color-text-muted)",
				},
				accent: {
					DEFAULT: "var(--color-accent)",
					hover: "var(--color-accent-hover)",
					light: "var(--color-accent-light)",
					dark: "var(--color-accent-dark)",
				},
				glass: {
					bg: "var(--glass-bg)",
					border: "var(--glass-border)",
				},
			},
			backgroundImage: {
				"gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
				"gradient-conic": "conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))",
				"gradient-primary": "var(--gradient-primary)",
				"gradient-glass": "var(--gradient-glass)",
			},
			backdropBlur: {
				glass: "12px",
			},
			boxShadow: {
				glass: "var(--glass-shadow)",
				"glass-hover": "var(--glass-shadow-hover)",
				"glow": "0 0 20px var(--color-accent)",
				"glow-lg": "0 0 40px var(--color-accent)",
			},
			borderRadius: {
				"2xl": "1rem",
				"3xl": "1.5rem",
			},
			animation: {
				"float": "float 6s ease-in-out infinite",
				"shimmer": "shimmer 1.5s infinite",
				"pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
				"slide-up": "slideUp 0.3s ease-out",
				"slide-down": "slideDown 0.3s ease-out",
				"fade-in": "fadeIn 0.3s ease-out",
			},
			keyframes: {
				float: {
					"0%, 100%": { transform: "translateY(0)" },
					"50%": { transform: "translateY(-10px)" },
				},
				shimmer: {
					"0%": { backgroundPosition: "200% 0" },
					"100%": { backgroundPosition: "-200% 0" },
				},
				slideUp: {
					"0%": { transform: "translateY(10px)", opacity: "0" },
					"100%": { transform: "translateY(0)", opacity: "1" },
				},
				slideDown: {
					"0%": { transform: "translateY(-10px)", opacity: "0" },
					"100%": { transform: "translateY(0)", opacity: "1" },
				},
				fadeIn: {
					"0%": { opacity: "0" },
					"100%": { opacity: "1" },
				},
			},
			transitionTimingFunction: {
				"bounce-in": "cubic-bezier(0.68, -0.55, 0.265, 1.55)",
			},
		},
	},
	plugins: [],
	darkMode: 'class',
};
export default config;
