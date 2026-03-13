<template>
  <NuxtLayout>
    <NuxtPage />
    <Toast />
    <ConfirmDialog :style="{ maxWidth: '50rem' }" />
  </NuxtLayout>
</template>

<script setup lang="ts">
import 'primeicons/primeicons.css'
import 'gridstack/dist/gridstack.min.css'
import { client } from './sdk/client/client.gen'

const { getToken } = useAuth()
const { t, locale } = useI18n()
const toast = useToast()
useNotificationPoller()
client.setConfig({
  baseURL: '/api/v1',
  auth: async () => {
    return await getToken()
  },
  onRequest: ({ options }) => {
    options.headers.set('lang', locale.value)
  },
  onResponseError: async ({ response }) => {
    console.error('This is the options on error', response)
    const rawDetail = response._data.detail
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
