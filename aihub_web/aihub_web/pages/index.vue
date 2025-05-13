<template>
  <div class="">
    <h1 class="w-full pb-32 pt-72 text-center text-6xl">
      {{ t('welcome') }}
    </h1>
    <DashboardGrid />
  </div>
</template>

<script setup lang="ts">
const { t } = useI18n()
</script>

<style scoped>

</style>
