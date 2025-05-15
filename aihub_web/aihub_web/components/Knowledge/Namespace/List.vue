<template>
  <div />
</template>

<script setup lang="ts">
import type { Namespace } from '@core/sdk/client'

const { t } = useI18n()

defineProps<{
  namespaces: Namespace[]
}>()

const emit = defineEmits<{
  selected: [namespace: Namespace]
}>()
</script>
