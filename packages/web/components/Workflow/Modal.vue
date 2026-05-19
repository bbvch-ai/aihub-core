<template>
  <Dialog
    :visible="modelValue"
    modal
    :header="header ?? t('agent.workflow.title')"
    :style="{ width: '90vw', height: '85vh' }"
    :content-style="{ height: '100%' }"
    @update:visible="emit('update:modelValue', $event)"
  >
    <div class="size-full">
      <WorkflowVisualization
        v-if="graphData && graphData.nodes && graphData.nodes.length"
        :graph-data="graphData"
      />
      <div
        v-else
        class="flex size-full items-center justify-center text-surface-500"
      >
        {{ t('agent.workflow.empty') }}
      </div>
    </div>
  </Dialog>
</template>

<script setup lang="ts">
import type { WorkflowGraph } from '@core/sdk/client'

const { t } = useI18n()

defineProps<{
  modelValue: boolean
  graphData: WorkflowGraph | null | undefined
  header?: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()
</script>
