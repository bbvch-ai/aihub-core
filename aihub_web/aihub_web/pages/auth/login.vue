<script setup lang="ts">
const login = () => {
  const { $auth } = useNuxtApp()
  $auth.signinRedirect()
}
</script>

<template>
  <div>
    <h1>Login</h1>
    <button @click="login">
      Sign In
    </button>
  </div>
</template>

<style scoped>

</style>
