import { createHtmlResponseGuard } from '@core/utils/apiResponseGuard'

import { client } from '~/sdk/client/client.gen'

// Route middleware runs before app.vue setup, including on an authenticated reload.
export default defineNuxtPlugin((nuxtApp) => {
  const { getToken } = useAuth()
  client.setConfig({
    baseURL: '/api/v1',
    auth: async () => await getToken(),
    onRequest: ({ options }) => {
      const locale = (nuxtApp.$i18n as { locale?: { value?: string } } | undefined)?.locale?.value
      if (locale) options.headers.set('lang', locale)
    },
    onResponse: createHtmlResponseGuard(nuxtApp),
  })
})
