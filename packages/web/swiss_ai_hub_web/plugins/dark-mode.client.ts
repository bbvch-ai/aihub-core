import { useDark } from '@vueuse/core'

export default defineNuxtPlugin(() => {
  useDark({ storageKey: 'dark' })
})
