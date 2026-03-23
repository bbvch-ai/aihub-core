import { definePreset } from '@primeuix/themes'
import Aura from '@primeuix/themes/aura'

const AIHubPreset = definePreset(Aura, {
  semantic: {
    primary: {
      50: '{surface.50}',
      100: '{surface.100}',
      200: '{surface.200}',
      300: '{surface.300}',
      400: '{surface.400}',
      500: '{surface.500}',
      600: '{surface.600}',
      700: '{surface.700}',
      800: '{surface.800}',
      900: '{surface.900}',
      950: '{surface.950}',
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
          100: '#ececec',
          200: '#e3e3e3',
          300: '#cdcdcd',
          400: '#b4b4b4',
          500: '#9b9b9b',
          600: '#676767',
          700: '#4e4e4e',
          800: '#333',
          850: '#262626',
          900: '#171717',
          950: '#0d0d0d',
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
          50: '#f9f9f9',
          100: '#ececec',
          200: '#e3e3e3',
          300: '#cdcdcd',
          400: '#b4b4b4',
          500: '#9b9b9b',
          600: '#676767',
          700: '#4e4e4e',
          800: '#333',
          850: '#262626',
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
  components: {
    datatable: {
      colorScheme: {
        light: {
          body: {
            cell: {
              selected: {
                border: {
                  color: '#ececec',
                },
              },
            },
          },
          row: {
            selected: {
              background: '#ececec',
              color: '#0d0d0d',
            },
          },
        },
        dark: {
          body: {
            cell: {
              selected: {
                border: {
                  color: '#262626',
                },
              },
            },
          },
          row: {
            selected: {
              background: '#262626',
              color: '#f9f9f9',
            },
          },
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
