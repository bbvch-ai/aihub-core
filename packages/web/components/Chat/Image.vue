<template>
  <img
    v-if="src"
    :src="src"
  >
</template>

<script setup lang="ts">
const props = defineProps<{
  url?: string | null
}>()

const { src } = useStoredImageUrl(() => props.url)
</script>
