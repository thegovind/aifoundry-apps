/** @type {import('tailwindcss').Config} */
export default {
    darkMode: ["class"],
    content: ["./index.html", "./src/**/*.{ts,tsx,js,jsx}"],
  theme: {
  	extend: {
  		fontFamily: {
  			'aptos': ['Aptos', 'system-ui', 'sans-serif'],
  			'monaspace': ['Monaspace Neon', 'monospace'],
  		},
  		borderRadius: {
  			lg: 'var(--radius)',
  			md: 'calc(var(--radius) - 2px)',
  			sm: 'calc(var(--radius) - 4px)'
  		},
  		colors: {
  			figma: {
  				black: 'rgb(var(--figma-black))',
  				'dark-gray': 'rgb(var(--figma-dark-gray))',
  				'medium-gray': 'rgb(var(--figma-medium-gray))',
  				'input-gray': 'rgb(var(--figma-input-gray))',
  				'light-gray': 'rgb(var(--figma-light-gray))',
  				'text-primary': 'rgb(var(--figma-text-primary))',
  				'text-secondary': 'rgb(var(--figma-text-secondary))',
  			},
  			azure: {
  				blue: 'rgb(var(--azure-blue))',
  				'blue-light': 'rgb(var(--azure-blue-light))',
  				'blue-dark': 'rgb(var(--azure-blue-dark))',
  				50: 'rgb(var(--azure-gray-50))',
  				100: 'rgb(var(--azure-gray-100))',
  				200: 'rgb(var(--azure-gray-200))',
  				300: 'rgb(var(--azure-gray-300))',
  				400: 'rgb(var(--azure-gray-400))',
  				500: 'rgb(var(--azure-gray-500))',
  				600: 'rgb(var(--azure-gray-600))',
  				700: 'rgb(var(--azure-gray-700))',
  				800: 'rgb(var(--azure-gray-800))',
  				900: 'rgb(var(--azure-gray-900))'
  			},
  			sidebar: {
  				DEFAULT: 'hsl(var(--sidebar-background))',
  				foreground: 'hsl(var(--sidebar-foreground))',
  				primary: 'hsl(var(--sidebar-primary))',
  				'primary-foreground': 'hsl(var(--sidebar-primary-foreground))',
  				accent: 'hsl(var(--sidebar-accent))',
  				'accent-foreground': 'hsl(var(--sidebar-accent-foreground))',
  				border: 'hsl(var(--sidebar-border))',
  				ring: 'hsl(var(--sidebar-ring))'
  			}
  		},
  		keyframes: {
  			'accordion-down': {
  				from: {
  					height: '0'
  				},
  				to: {
  					height: 'var(--radix-accordion-content-height)'
  				}
  			},
  			'accordion-up': {
  				from: {
  					height: 'var(--radix-accordion-content-height)'
  				},
  				to: {
  					height: 'var(--radix-accordion-content-height)'
  				}
  			}
  		},
  		animation: {
  			'accordion-down': 'accordion-down 0.2s ease-out',
  			'accordion-up': 'accordion-up 0.2s ease-out'
  		}
  	}
  },
  plugins: [import("tailwindcss-animate")],
}

