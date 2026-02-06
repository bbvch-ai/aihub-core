<template>
  <div>
    <Divider class="my-4" />
    <div class="max-h-96 overflow-auto break-words rounded-lg border bg-surface-0 p-4 dark:border-surface-700 dark:bg-surface-900">
      <Tree
        :value="treeData"
        selection-mode="single"
        :meta-key-selection="false"
      >
        <template #default="{ node }">
          <div class="flex items-center gap-2">
            <Icon
              v-if="node.type === 'string'"
              name="mage:message"
              class="size-3 text-surface-600 dark:text-surface-400"
            />
            <Icon
              v-else-if="node.type === 'number'"
              name="mage:hash"
              class="size-3 text-surface-600 dark:text-surface-400"
            />
            <Icon
              v-else-if="node.type === 'boolean'"
              name="mage:check-circle"
              class="size-3 text-surface-600 dark:text-surface-400"
            />
            <Icon
              v-else-if="node.type === 'null'"
              name="mage:cancel"
              class="size-3 text-surface-500 dark:text-surface-500"
            />
            <Icon
              v-else-if="node.type === 'array'"
              name="mage:arrowlist"
              class="size-3 text-surface-600 dark:text-surface-400"
            />
            <Icon
              v-else-if="node.type === 'object'"
              name="mage:box"
              class="size-3 text-surface-600 dark:text-surface-400"
            />
            <span class="font-mono text-sm">{{ node.label }}</span>
          </div>
        </template>
      </Tree>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { ContextualizedAgentEvent } from '@core/sdk/client'
import type { TreeNode } from 'primevue/treenode'

interface Props {
  event: ContextualizedAgentEvent
}

const props = defineProps<Props>()

const { convertJsonToTree } = useJsonTree()

const treeData = computed<TreeNode[]>(() => {
  const eventData = props.event.event || props.event
  return convertJsonToTree(eventData, 'event', {
    maxDepth: 8,
    expandLevel: 2,
  })
})
</script>
