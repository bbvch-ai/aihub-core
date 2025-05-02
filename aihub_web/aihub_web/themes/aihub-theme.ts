import { definePreset } from '@primeuix/themes'
import Aura from '@primeuix/themes/aura'

const AIHubPreset = definePreset(Aura, {
  semantic: {
    primary: {
      50: '{red.50}',
      100: '{red.100}',
      200: '{stone.200}',
      300: '{red.300}',
      400: '{red.400}',
      500: '{red.500}',
      600: '{red.600}',
      700: '{red.700}',
      800: '{red.800}',
      900: '{red.900}',
      950: '{red.950}',
    },
    colorScheme: {
      light: {
        primary: {
          color: '{stone.950}',
          inverseColor: '#ffffff',
          hoverColor: '{stone.900}',
          activeColor: '{stone.800}',
        },
        surface: {
          50: '#f9f9f9',
        },
        highlight: {
          background: '{stone.950}',
          focusBackground: '{stone.700}',
          color: '#ffffff',
          focusColor: '#ffffff',
        },
      },
      dark: {
        primary: {
          color: '{stone.50}',
          inverseColor: '{stone.950}',
          hoverColor: '{stone.100}',
          activeColor: '{stone.200}',
        },
        surface: {
          900: '#171717',
          950: '#0d0d0d',
        },
        highlight: {
          background: 'rgba(250, 250, 250, .16)',
          focusBackground: 'rgba(250, 250, 250, .24)',
          color: 'rgba(255,255,255,.87)',
          focusColor: 'rgba(255,255,255,.87)',
        },
      },
    },
  },
})

export default {
  preset: AIHubPreset,
  options: {
    darkModeSelector: '.dark',
  },
}
