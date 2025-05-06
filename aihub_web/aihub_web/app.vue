<template>
  <NuxtLayout>
    <NuxtPage />
  </NuxtLayout>
</template>

<script setup lang="ts">
import 'primeicons/primeicons.css'
import { client } from './sdk/client/client.gen'

const { getToken } = useAuth()
const { locale } = useI18n()

client.setConfig({
  baseURL: '/api/v1',
  auth: async () => {
    return await getToken()
  },
  onRequest: ({ options }) => {
    console.log('Request with lang', locale.value)
    options.headers.set('lang', locale.value)
  },
})
</script>
