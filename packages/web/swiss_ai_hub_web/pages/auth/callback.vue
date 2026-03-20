<template>
  <div class="flex min-h-screen items-center justify-center bg-zinc-900 text-white">
    <div
      v-if="loading"
      class="text-center"
    >
      <h1 class="mb-4 text-2xl">
        {{ t('auth.callback.loggingIn') }}
      </h1>
      <div class="mx-auto size-12 animate-spin rounded-full border-y-2 border-white" />
    </div>

    <div
      v-else-if="error"
      class="text-center"
    >
      <h1 class="mb-4 text-2xl text-red-500">
        {{ t('auth.callback.loginError') }}
      </h1>
      <p>{{ error }}</p>
      <p class="mt-4">
        {{ t('auth.callback.redirectingToLogin') }}
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
const { $auth } = useNuxtApp()
const error = ref(null)
const loading = ref(true)

definePageMeta({
  layout: 'anonymous',
})

const { t, locale } = useI18n()

// Add proper error handling
$auth.signinRedirectCallback()
  .then(() => {
    console.log('Successfully processed authentication callback')
    navigateTo('/')
  })
  .catch((err) => {
    console.error('Error during authentication callback:', err)
    error.value = err.message || t('auth.callback.genericError')
    // After 3 seconds, redirect to login page
    setTimeout(() => {
      navigateTo(`/${locale.value}/auth/login`)
    }, 3000)
  })
  .finally(() => {
    loading.value = false
  })
</script>
