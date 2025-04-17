<template>
  <Card class="!rounded-2xl bg-surface-50 dark:!bg-surface-800">
    <template #header>
      <div class="absolute -top-3 right-12 rounded bg-surface-50 px-2 py-1 text-xs font-semibold dark:!bg-surface-800">
        {{ event.agent_class }}
      </div>
    </template>
    <template #content>
      <Panel
        toggleable
        collapsed
        class="panel border-none bg-transparent"
      >
        <template #header>
          <div class="relative flex flex-row gap-4">
            <div class="w-8 pt-1">
              <Icon
                :name="icon ?? 'hugeicons:question'"
                class="size-5"
              />
            </div>
            <div>
              <p class="text-xl font-bold">
                {{ event.event_display_name }}
              </p>
              <p class="text-sm text-surface-800 dark:text-surface-200">
                {{ event.event_display_description }}
              </p>
            </div>
          </div>
        </template>
        <div class="pt-4">
          <Divider />
          <br>
          <slot />
        </div>
      </Panel>
    </template>
  </Card>
</template>

<script setup lang="ts">
import type { WsServerEvent } from '@core/sdk/client'

defineProps<{
  event: WsServerEvent
  icon: string
}>()
</script>

<style scoped>
::v-deep(.panel) {
  .p-panel-header {
    padding: 0 !important;
  }
}
</style>
