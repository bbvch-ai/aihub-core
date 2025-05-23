<template>
  <NuxtLayout>
    <NuxtPage />
  </NuxtLayout>
</template>

<script setup lang="ts">
import 'primeicons/primeicons.css'
import 'gridstack/dist/gridstack.min.css'
import { client } from './sdk/client/client.gen'

const { getToken } = useAuth()
const { locale } = useI18n()

client.setConfig({
  baseURL: '/api/v1',
  auth: async () => {
    return await getToken()
  },
  onRequest: ({ options }) => {
    options.headers.set('lang', locale.value)
  },
})
</script>
