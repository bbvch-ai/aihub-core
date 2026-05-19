<template>
  <div class="hierarchy w-full overflow-x-auto">
    <OrganizationChart
      :value="chartData"
      collapsible
      :selection-mode="'single'"
      @node-select="toNode"
    >
      <template #thread="{ node }">
        <span>{{ node.data.name }}</span>
      </template>

      <template #display="{ node }">
        <div class="flex flex-col gap-2">
          <Tag
            :value="formattedDate(node.data.started_at)"
            severity="secondary"
          />
          <Badge :value="node.data.duration + 's'" />
        </div>
      </template>

      <template #run="{ node }">
        <div class="flex flex-col gap-2">
          <AgentAvatar :agent="node.data.agent" />
          <Tag
            v-if="node.data.has_pending"
            severity="warn"
            :value="pendingType(node.data)"
          />
          <Tag
            v-else
            severity="success"
            value="Completed"
          />
          <Tag
            v-if="node.data.has_errors"
            severity="danger"
            value="Error"
          />
          <Tag
            v-else
            severity="success"
            value="No Errors"
          />
        </div>
      </template>
    </OrganizationChart>
  </div>
</template>

<script setup lang="ts">
import { format } from 'date-fns'
import OrganizationChart, { type OrganizationChartNode } from 'primevue/organizationchart'
import { computed } from 'vue'

import type { ThreadDto, DisplayStatistics, RunStatistics } from '@core/sdk/client'

// Define the props
const props = defineProps<{
  thread: ThreadDto
}>()

const router = useRouter()
const tenantPath = useTenantPath()
const { pendingType } = useThreadUtils()

const toNode = (node: OrganizationChartNode) => {
  let displayId: string | undefined
  if (node.data.display_id) {
    displayId = node.data.display_id
  }
  if (node.data.run_id) {
    const display = props.thread.displays?.find((display: DisplayStatistics) => {
      return display?.runs?.some((run: RunStatistics) => run.run_id === node.data.run_id)
    })
    displayId = display?.display_id
  }
  if (displayId) {
    router.push(tenantPath(`/service/threads/${props.thread.id}/display/${displayId}`))
  }
  else {
    router.push(tenantPath(`/service/threads/${props.thread.id}/display`))
  }
}

const formattedDate = (datestr: string) => format(new Date(datestr), 'yyyy.MM.dd HH:mm')

// Computed property to transform ThreadDto into OrganizationChart data structure
const chartData = computed<OrganizationChartNode>(() => {
  if (!props.thread) return {} as OrganizationChartNode

  // Function to transform RunStatistics
  const mapRun = (run: RunStatistics): OrganizationChartNode => ({
    key: run.run_id,
    type: 'run',
    data: run,
    children: [],
  })

  // Function to transform DisplayStatistics
  const mapDisplay = (display: DisplayStatistics): OrganizationChartNode => ({
    key: display.display_id,
    type: 'display',
    data: display,
    children: (display.runs ?? []).map(mapRun),
  })

  // Transform the main thread data
  const rootNode: OrganizationChartNode = {
    key: props.thread.id,
    type: 'thread',
    data: props.thread,
    children: (props.thread.displays ?? []).map(mapDisplay),
  }
  return rootNode
})
</script>

<style scoped>
/* Add some basic styling for better readability */
.hierarchy :deep(.p-organizationchart-node-content) {
  padding: 0;
  border: none;
}

.hierarchy :deep(.p-organizationchart-line-down) {
  background-color: #adb5bd; /* primevue gray-400 */
}
.hierarchy :deep(.p-organizationchart-line-left) {
  border-right: 1px solid #adb5bd;
}
.hierarchy :deep(.p-organizationchart-line-top) {
  border-top: 1px solid #adb5bd;
}
</style>
