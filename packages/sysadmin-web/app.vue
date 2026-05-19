<template>
  <NuxtLayout>
    <NuxtPage />
    <Toast />
    <ConfirmDialog />
  </NuxtLayout>
</template>

<script setup lang="ts">
import 'primeicons/primeicons.css'
import { client } from './sdk/client/client.gen'

const { getToken } = useAuth()
const { t, locale } = useI18n()
const localePath = useLocalePath()
const toast = useToast()

// The sysadmin-web SDK talks to sysadmin-api at /api/v1 (same origin —
// sysadmin.${DOMAIN}/api/v1 — proxied to localhost:8001 in dev).
client.setConfig({
  baseURL: '/api/v1',
  auth: async () => {
    return await getToken()
  },
  onRequest: ({ options }) => {
    options.headers.set('lang', locale.value)
  },
  onResponseError: async ({ response }) => {
    console.error('Sysadmin API error', response.status, response._data?.detail)

    // Non-sysadmin trying to reach an endpoint → bounce to tenant selection
    // on the main app (cross-origin) so they land somewhere they can act on.
    if (response.status === 403) {
      const config = useRuntimeConfig()
      const mainUrl = config.public.mainApi.url
      if (mainUrl && import.meta.client) {
        window.location.href = `${mainUrl}${localePath('/select-tenant')}`
        return
      }
    }

    const rawDetail = response._data?.detail
    const message = typeof rawDetail === 'object' && rawDetail?.message
      ? rawDetail.message
      : rawDetail
    toast.add({
      severity: 'error',
      summary: t(`http_error.code.${response.status}`),
      detail: message,
      life: 10_000,
    })
  },
})
</script>
