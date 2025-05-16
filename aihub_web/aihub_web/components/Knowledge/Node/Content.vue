<template>
  <div class="rounded-lg border border-transparent px-2 pb-2 hover:border-surface-100 hover:shadow-lg hover:dark:border-surface-800">
    <MarkdownRenderer
      :md="node.text"
    />
  </div>
</template>

<script setup lang="ts">
import type { NodeDto } from '@core/sdk/client'

defineProps<{
  node: NodeDto
}>()
</script>

<style scoped>

</style>
