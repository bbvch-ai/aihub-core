<template>
  <img
    v-if="src"
    :src="src"
    :alt="t('chat.image')"
  >
</template>

<script setup lang="ts">
const props = defineProps<{
  url?: string | null
}>()

const { t } = useI18n()
const { src } = useStoredImageUrl(() => props.url)
</script>
