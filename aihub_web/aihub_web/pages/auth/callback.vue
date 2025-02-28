<template>
  <div class="flex items-center justify-center min-h-screen bg-zinc-900 text-white">
    <div
      v-if="loading"
      class="text-center"
    >
      <h1 class="text-2xl mb-4">
        Logging you in...
      </h1>
      <div class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-white mx-auto" />
    </div>

    <div
      v-else-if="error"
      class="text-center"
    >
      <h1 class="text-2xl mb-4 text-red-500">
        Login Error
      </h1>
      <p>{{ error }}</p>
      <p class="mt-4">
        Redirecting to login page...
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
const { $auth, $i18n } = useNuxtApp()
const error = ref(null)
const loading = ref(true)

definePageMeta({
  layout: 'anonymous',
})

// Add proper error handling
$auth.signinRedirectCallback()
  .then(() => {
    console.log('Successfully processed authentication callback')
    navigateTo('/')
  })
  .catch((err) => {
    console.error('Error during authentication callback:', err)
    error.value = err.message || 'An error occurred during login. Please try again.'
    // After 3 seconds, redirect to login page
    setTimeout(() => {
      navigateTo(`/${$i18n.locale.value}/auth/login`)
    }, 3000)
  })
  .finally(() => {
    loading.value = false
  })
</script>
