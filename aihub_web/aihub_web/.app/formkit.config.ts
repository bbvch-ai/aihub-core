import { en, de, fr, it } from '@formkit/i18n'
import { primeInputs } from '@sfxcode/formkit-primevue'

import type { DefaultConfigOptions } from '@formkit/vue'

const config: DefaultConfigOptions = {
  inputs: primeInputs,
  locales: { en, de, fr, it },
  locale: 'en',

}

export default config
