<template>
  <div class="flex w-full justify-center">
    <div class="flex w-full max-w-screen-2xl flex-col gap-2 p-4">
      <div class="flex justify-end">
        <div class="pr-4">
          <Button
            type="button"
            :label="t('dashboard.add_widget')"
            icon="pi pi-plus"
            @click="($event) => newWidget.toggle($event)"
          />
          <Popover ref="newWidget">
            <div class="flex flex-col gap-2">
              <p class="font-bold">
                {{ t("dashboard.create_widget") }}
              </p>
              <SelectButton
                v-model="component"
                size="small"
                option-label="label"
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
                :placeholder="t('dashboard.select_data_type')"
              />
              <Select
                v-model="agent"
                :options="agentInstances"
                option-label="agent_config.name"
                :placeholder="t('dashboard.select_agent')"
                :loading="agentInstancesAreLoading"
                show-clear
              />
              <Button
                :label="t('dashboard.create')"
                :disabled="!(timeRange && event)"
                @click="addWidget"
              />
            </div>
          </Popover>
        </div>
      </div>
      <div
        ref="gridstack"
        class="min-h-[400px]"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { GridStack } from 'gridstack'
import { v4 as uuid } from 'uuid'
import { h, render } from 'vue'

import 'gridstack/dist/gridstack.min.css'
import GridItemVue from './Item.vue'

import type { FullAgentInstanceDto, TimeRange } from '@core/sdk/client'
import type { DashboardWidget } from '@core/types/DashboardWidget'
import type { GridStackElement } from 'gridstack'

const { agentInstances, agentInstancesAreLoading } = useAgentInstances()
const { t } = useI18n()
const { myUser, myUserIsLoading } = useMyUser()
const { saveDashboard } = useSaveDashboard()

watch(myUser, () => {
  if (myUser.value?.dashboard?.children && grid) {
    grid.load(myUser.value?.dashboard?.children ?? [])
  }
})

const gridStackElement = templateRef('gridstack')
let grid: GridStack | null = null
const itemRenderContexts = new Map<string, HTMLElement>()

const nuxtApp = useNuxtApp()

onMounted(() => {
  grid = GridStack.init({
    cellHeight: '350px',
    minRow: 1,
    margin: '24px',
    column: 4,
  }, gridStackElement.value)

  GridStack.addRemoveCB = (_: HTMLElement, w: DashboardWidget, add: boolean): GridStackElement | undefined => {
    const widgetId = w.id

    if (add) {
      const tempRenderHost = document.createElement('div')

      const vueComponentVNode = h(
        GridItemVue,
        {
          component: w.component,
          data: w,
          onRemove: (domElementToRemove: HTMLElement) => {
            if (grid && domElementToRemove) {
              grid.removeWidget(domElementToRemove)
            }
          },
        },
      )

      if (nuxtApp && nuxtApp.vueApp) {
        vueComponentVNode.appContext = nuxtApp.vueApp._context
      }

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

  if (!myUserIsLoading.value) {
    grid.load(myUser.value?.dashboard?.children ?? [])
  }

  grid.on('change', () => {
    saveLayout()
  })

  grid.on('added', () => {
    saveLayout()
  })

  grid.on('removed', () => {
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
    saveDashboard({ grid: serializedData })
  }
}

const newWidget = templateRef('newWidget')

type componentSelection = { label: string, component: string, w: number, h: number }
const componentOptions = ref<componentSelection[]>([
  { label: 'Number', component: 'DashboardComponentNumber', w: 1, h: 1 },
  { label: 'Line Chart', component: 'DashboardComponentLineChart', w: 2, h: 1 },
  { label: 'Bar Chart', component: 'DashboardComponentBarChart', w: 2, h: 1 },
])
const component = ref<componentSelection>(componentOptions.value[0])

const timeRange = ref<TimeRange>('24h')
const timeRanges = ref<string[]>(['1h', '24h', '30d', '365d'])

const agent = ref<FullAgentInstanceDto | null>(null)

type eventType = { label: string, event: string }
const eventOptions = computed<eventType[]>(() => {
  return [
    'StartEvent',
    'UserMessageEvent',
    'ExceptionEvent',
    'HumanInTheLoopRequestEvent',
    'BotInTheLoopRequestEvent',
    'AgentInTheLoopRequestEvent',
  ].map((event: string) => ({
    event,
    label: t(`dashboard.events.${event}.label`),
  }))
})
const event = ref<eventType | null>(null)

const addWidget = () => {
  if (!grid) return
  const newWidgetNodeToAdd: DashboardWidget = {
    id: uuid(),
    component: component.value.component,
    w: component.value.w,
    h: component.value.h,
    noResize: true,
    timeRange: timeRange.value,
    agent: agent.value ? { agentId: agent.value.agent_id, agentClass: agent.value.agent_class } : undefined,
    event: event.value!.event,
  }
  grid.addWidget(newWidgetNodeToAdd)
}
</script>
