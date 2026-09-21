<template>
  <NuxtLayout>
    <NuxtPage />
    <Toast />
    <ConfirmDialog />
    <div
      v-if="homeResolving"
      class="fixed inset-0 z-50 flex items-center justify-center bg-white dark:bg-surface-900"
    >
      <ProgressSpinner />
    </div>
  </NuxtLayout>
</template>

<script setup lang="ts">
import 'primeicons/primeicons.css'
import 'gridstack/dist/gridstack.min.css'
import { client } from './sdk/client/client.gen'

const { getToken } = useAuth()
const { t, locale } = useI18n()
const localePath = useLocalePath()
const route = useRoute()
const toast = useToast()
useNotificationPoller()

// Overlay lives at the root, not the page: the home-redirect middleware
// redirects before any page mounts, so the page can't show it.
const homeResolving = useHomeResolving()
client.setConfig({
  baseURL: '/api/v1',
  auth: async () => {
    return await getToken()
  },
  onRequest: ({ options }) => {
    options.headers.set('lang', locale.value)
  },
  onResponseError: async ({ response }) => {
    console.error('API error', response.status, response._data?.detail)

    // Invalid or inaccessible tenant → redirect to tenant selection
    if (response.status === 403 && response._data?.detail === 'Access denied') {
      await navigateTo(localePath('/select-tenant'), { replace: true })
      return
    }

    // Suppress error toasts on pages without tenant context (login, select-tenant, callback)
    if (!route.params.tenant) return

    const rawDetail = response._data?.detail

    let message = rawDetail

    if (Array.isArray(rawDetail) && rawDetail.every(e => typeof e.msg === 'string')) {
      message = rawDetail.map(e => e.msg).join('\n')
    }
    else if (typeof rawDetail === 'object' && rawDetail?.message) {
      message = rawDetail.message
    }

    toast.add({
      severity: 'error',
      summary: t(`http_error.code.${response.status}`),
      detail: message,
      life: 10_000,
    })
  },
})
</script>
