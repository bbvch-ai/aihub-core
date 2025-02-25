<template>
  <NuxtLayout>
    <NuxtPage />
  </NuxtLayout>
</template>

<script setup lang="ts">
import 'primeicons/primeicons.css'
import { client } from './sdk/client/client.gen'

const { getToken } = useAuth()

client.setConfig({
  baseURL: '/api/v1',
  auth: async () => {
    return await getToken()
  },
})
</script>
