<script setup lang="ts">
const { $auth } = useNuxtApp()

$auth.signinRedirectCallback()
  .then(() => {
    navigateTo('/')
  })
</script>

<template>
  <div>
    <h1>Logging you in...</h1>
  </div>
</template>

<style scoped>

</style>
