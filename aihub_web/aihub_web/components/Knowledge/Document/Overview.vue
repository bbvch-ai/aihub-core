<template>
  <div>
    <div class="flex justify-between text-xs opacity-60">
      <div>{{ document.title }}</div>
      <div>{{ createdAt }}</div>
    </div>
    <Divider />
    <slot />
    <Divider />
    <div class="flex justify-between text-xs opacity-60">
      <div>Namespace: {{ document.namespace }}</div>
      <div>Pages: {{ document.number_of_pages }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { DocumentDto } from '@core/sdk/client'

const props = defineProps<{
  document: DocumentDto
}>()

const { t } = useI18n()

const createdAt = computed(() => {
  return useDateFormat(new Date(props.document.created_at), 'DD.MM.YYYY HH:mm:ss')
})
</script>
