<template>
  <div
    class="group relative rounded-lg border border-surface-200 bg-white p-4 dark:border-surface-700 dark:bg-surface-800"
    :class="{ 'opacity-50': !active }"
  >
    <Tag
      v-if="node.score"
      v-tooltip="scoreText"
      class="absolute right-1 top-1 hidden text-xs group-hover:block"
      :class="{ '!block': alwaysShowScore }"

      :value="scoreRank"
      :severity="scoreColor"
    />
    <MarkdownRenderer
      :md="node.content"
    />
  </div>
</template>

<script setup lang="ts">
import type { IngestedNode } from '@core/sdk/client'

const props = withDefaults(defineProps<{
  node: IngestedNode
  alwaysShowScore?: boolean
  active?: boolean
}>(), {
  alwaysShowScore: false,
  active: true,
})

const scoreColor = computed<string>(() => {
  const score = props.node.score
  if (!score) return ''
  if (score <= 0.5) {
    return 'danger'
  }
  if (score <= 0.85) {
    return 'warn'
  }
  return 'success'
})

const scoreText = computed<string>(() => {
  const score = props.node.score
  if (!score) return ''
  return `Relevance: ${Math.round(score * 100)}%`
})

const scoreRank = computed<string>(() => {
  const score = props.node.score
  if (!score) return ''
  if (score <= 0.5) {
    return 'D'
  }
  if (score <= 0.75) {
    return 'C'
  }
  if (score <= 0.85) {
    return 'B'
  }
  if (score <= 0.90) {
    return 'A'
  }
  if (score <= 0.95) {
    return 'A+'
  }
  return 'A++'
})
</script>
