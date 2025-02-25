<template>
  <div>Processing silent token renewal...</div>
</template>

<script setup lang="ts">
import { useNuxtApp } from '#app'

const { $auth } = useNuxtApp()

$auth.signinSilentCallback()
  .catch((error) => {
    console.error('Silent renew error:', error)
  })
</script>
