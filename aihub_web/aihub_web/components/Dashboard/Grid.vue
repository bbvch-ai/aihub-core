<template>
  <div class="flex flex-col gap-2 p-4">
    <div class="flex justify-end">
      <div>
        <Button
          type="button"
          label="Add"
          @click="($event) => newWidget.toggle($event)"
        />
        <Popover ref="newWidget">
          <div class="flex flex-col gap-2">
            <p class="font-bold">
              Create new Widget
            </p>
            <SelectButton
              v-model="component"
              size="small"
              option-label="label"
              option-value="component"
              :options="componentOptions"
              :allow-empty="false"
            />
            <SelectButton
              v-model="timeRange"
              size="small"
              :options="timeRanges"
              :allow-empty="false"
            />
            <Select
              v-model="event"
              :options="eventOptions"
              option-label="label"
              option-value="event"
              placeholder="Select Data type"
            />
            <Select
              v-model="agent"
              :options="agents"
              option-label="agent_config.name"
              placeholder="Select an Agent (Optional)"
              :loading="agentsAreLoading"
            />
            <Button
              label="Create"
              :disabled="!(timeRange && event)"
              @click="addWidget"
            />
          </div>
        </Popover>
      </div>
    </div>
    <div
      ref="gridstack"
      class="min-h-[200px]"
    />
  </div>
</template>

<script setup lang="ts">
import { GridStack } from 'gridstack'
import { h, render } from 'vue'

import 'gridstack/dist/gridstack.min.css'
import GridItemVue from './Item.vue'

import type { AgentDto, TimeRange } from '@core/sdk/client'
import type { DashboardWidget } from '@core/types/DashboardWidget'
import type { GridStackElement } from 'gridstack'

const { agents, agentsAreLoading } = useAgents()
const { componentNames } = useDashboardComponent()

const gridStackElement = templateRef('gridstack')
let grid: GridStack | null = null
const itemRenderContexts = new Map<string, HTMLElement>()

const initialWidgets: DashboardWidget[] = []

onMounted(() => {
  grid = GridStack.init({
    float: true,
    cellHeight: '80px',
    minRow: 1,
    margin: 10,
  }, gridStackElement.value)

  GridStack.addRemoveCB = (_: HTMLElement, w: DashboardWidget, add: boolean): GridStackElement | undefined => {
    const widgetId = w.id

    if (add) {
      const tempRenderHost = document.createElement('div')

      const vueComponentVNode = h(
        GridItemVue,
        {
          component: w.component,
          title: w.title,
          data: w,
          onRemove: (domElementToRemove: HTMLElement) => {
            if (grid && domElementToRemove) {
              grid.removeWidget(domElementToRemove)
            }
          },
        },
      )

      render(vueComponentVNode, tempRenderHost)
      itemRenderContexts.set(widgetId, tempRenderHost)
      return vueComponentVNode.el as GridStackElement
    }
    else {
      const contextHostToUnmount = itemRenderContexts.get(widgetId)
      if (contextHostToUnmount) {
        render(null, contextHostToUnmount)
        itemRenderContexts.delete(widgetId)
      }
    }
  }

  grid.load(initialWidgets)

  grid.on('change', () => {
    saveLayout()
  })
})

onBeforeUnmount(() => {
  if (grid) {
    itemRenderContexts.forEach(host => render(null, host))
    itemRenderContexts.clear()
    grid.destroy(false)
    grid = null
    GridStack.addRemoveCB = undefined
  }
})

const saveLayout = () => {
  if (grid) {
    const serializedData = grid.save(true, true)
    console.log('Saved Layout:', JSON.stringify(serializedData, null, 2))
  }
}

const newWidget = templateRef('newWidget')
const component = ref<string>('DashboardComponentNumber')
const componentOptions = ref<{ label: string, component: string }[]>([
  { label: 'Number', component: 'DashboardComponentNumber' },
  { label: 'Chart', component: 'DashboardComponentChart' },
])
const timeRange = ref<TimeRange>('24h')
const timeRanges = ref<string[]>(['1h', '24h', '30d', '365d'])
const agent = ref<AgentDto | null>(null)
const eventOptions = computed<{ label: string, event: string }[]>(() => [
  { label: 'Starts', event: 'StartEvent' },
])
const event = ref<string>('')
const addWidget = () => {
  if (!grid) return
  const newWidgetNodeToAdd: DashboardWidget = {
    id: 'temporary',
    title: 'Test',
    component: component.value,
    timeRange: timeRange.value,
    agent: agent.value ? { agentId: agent.value.agent_id, agentClass: agent.value.agent_class } : undefined,
    event: event.value,
  }
  grid.addWidget(newWidgetNodeToAdd)
}
</script>
