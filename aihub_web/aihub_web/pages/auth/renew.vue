<template>
  <div class="hidden">
    Processing silent token renewal...
  </div>
</template>

<script setup lang="ts">
const { $auth } = useNuxtApp()

definePageMeta({
  layout: 'anonymous',
})

// Add proper error handling for silent renewal
$auth.signinSilentCallback()
  .then(() => {
    console.log('Silent token renewal successful')
  })
  .catch((error) => {
    console.error('Silent token renewal error:', error)
    // We don't redirect here as this is in an iframe
    // The parent window should handle the error via the event handlers
  })
</script>

<style scoped>
/* Hide this page since it's loaded in an iframe */
.hidden {
  display: none;
}
</style>
