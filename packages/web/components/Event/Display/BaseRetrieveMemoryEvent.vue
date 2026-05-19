<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="lucide:brain"
  >
    <div class="flex flex-col gap-6">
      <!-- Retrieved Memories Section -->
      <div
        v-if="event.event.memories?.length"
        class="flex flex-col gap-3"
      >
        <div class="flex items-center gap-2 text-sm font-semibold text-surface-700 dark:text-surface-300">
          <Icon
            name="lucide:brain"
            class="size-4"
          />
          <span>{{ t('event.retrieveMemory.memories') }} ({{ event.event.memories.length }})</span>
        </div>

        <div
          v-for="memory in event.event.memories"
          :key="memory.id"
          class="flex flex-col gap-2 rounded-lg border border-surface-200 bg-surface-50 p-4 dark:border-surface-700 dark:bg-surface-800"
        >
          <div class="text-base">
            {{ memory.memory }}
          </div>
          <div class="flex items-center gap-4 text-xs text-surface-500 dark:text-surface-400">
            <span
              v-if="memory.score != null"
              class="flex items-center gap-1"
            >
              <Icon
                name="lucide:star"
                class="size-3"
              />
              {{ t('event.retrieveMemory.score') }}: {{ memory.score.toFixed(2) }}
            </span>
            <span class="flex items-center gap-1">
              <Icon
                name="lucide:calendar"
                class="size-3"
              />
              {{ formatDate(memory.created_at) }}
            </span>
          </div>
        </div>
      </div>

      <div
        v-else
        class="text-sm text-surface-500 dark:text-surface-400"
      >
        {{ t('event.retrieveMemory.noMemories') }}
      </div>

      <!-- Knowledge Graph Section -->
      <div
        v-if="event.event.relations?.length"
        class="flex flex-col gap-3"
      >
        <div class="flex items-center gap-2 text-sm font-semibold text-surface-700 dark:text-surface-300">
          <Icon
            name="lucide:network"
            class="size-4"
          />
          <span>{{ t('event.retrieveMemory.relations') }} ({{ event.event.relations.length }})</span>
        </div>

        <div class="rounded-lg border border-surface-200 dark:border-surface-700">
          <MemoryGraph
            :relations="event.event.relations"
            height="300px"
          />
        </div>
      </div>
    </div>
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type { BaseRetrieveMemoryEventReadable, ThreadDto, AgentEventReadable } from '@core/sdk/client'

defineProps<{
  event: AgentEventReadable & { event: BaseRetrieveMemoryEventReadable }
  thread: ThreadDto
}>()

const { t } = useI18n()

const formatDate = (dateString: string): string => {
  try {
    const date = new Date(dateString)
    return date.toLocaleString()
  }
  catch {
    return dateString
  }
}
</script>
