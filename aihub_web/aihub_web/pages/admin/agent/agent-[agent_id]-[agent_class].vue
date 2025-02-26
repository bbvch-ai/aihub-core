<template>
  {{ route.params.agent_id }}
  {{ route.params.agent_class }}
</template>

<script setup lang="ts">
const route = useRoute()
</script>

<style scoped>

</style>
