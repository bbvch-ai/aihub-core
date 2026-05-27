<template>
  <div class="hidden">
    {{ t('auth.renew.processing') }}
  </div>
</template>

<script setup lang="ts">
const { $auth } = useNuxtApp()

definePageMeta({
  layout: 'anonymous',
})

const { t } = useI18n()

await $auth.signinSilentCallback()
</script>

<style scoped>
/* Hide this page since it's loaded in an iframe */
.hidden {
  display: none;
}
</style>
