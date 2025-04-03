<template>
  <Card class="!rounded-2xl bg-surface-50 dark:!bg-surface-800">
    <template #content>
      <Panel
        toggleable
        collapsed
        class="border-none bg-transparent"
      >
        <template #header>
          <div>
            <p class="text-xl font-bold">
              {{ title }}
            </p>
            <p class="text-sm text-surface-800 dark:text-surface-200">
              {{ subtitle }}
            </p>
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
  title: string
  subtitle: string
}>()
</script>
