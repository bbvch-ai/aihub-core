<template>
  <FormKitDynamicConfiguration
    :form="form"
    :initial-data="initialData"
    @submit="emit('submit', $event)"
  />
</template>

<script setup lang="ts">
import type { FormkitElement } from '@core/sdk/client'

defineProps<{
  form: FormkitElement[]
  initialData?: Record<string, unknown>
}>()

const emit = defineEmits<{
  submit: [Record<string, unknown>]
}>()
</script>
