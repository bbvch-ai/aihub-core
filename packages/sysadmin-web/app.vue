<template>
  <NuxtLayout>
    <NuxtPage />
    <Toast />
    <ConfirmDialog />
  </NuxtLayout>
</template>

<script setup lang="ts">
import 'primeicons/primeicons.css'
import { createHtmlResponseGuard } from '@core/utils/apiResponseGuard'

import { client } from './sdk/client/client.gen'

const { getToken } = useAuth()
const { t, locale } = useI18n()
const toast = useToast()
const nuxtApp = useNuxtApp()

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
  // The layer plugin installs this on the @swiss-ai-hub/web client only. This
  // is a separate client instance generated from the sysadmin-api spec, and
  // sysadmin.${DOMAIN}/api/v1 falls through to the same SPA shell when
  // sysadmin-api is down.
  onResponse: createHtmlResponseGuard(nuxtApp),
  onResponseError: async ({ response }) => {
    console.error('Sysadmin API error', response.status, response._data?.detail)

    // The sysadmin.global middleware is authoritative for role gating, so a
    // 403 here only fires in narrow defence-in-depth cases (role revoked
    // mid-session). Surface it as a toast and let the user navigate; no
    // implicit cross-origin redirect.
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
