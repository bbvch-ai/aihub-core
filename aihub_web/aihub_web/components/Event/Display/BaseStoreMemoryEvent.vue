<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="lucide:database-zap"
  >
    <div class="flex flex-col gap-6">
      <!-- Memory Changes Section -->
      <div
        v-if="hasMemoryChanges"
        class="flex flex-col gap-4"
      >
        <div class="flex items-center gap-2 text-sm font-semibold text-surface-700 dark:text-surface-300">
          <Icon
            name="lucide:file-edit"
            class="size-4"
          />
          <span>{{ t('event.storeMemory.title') }}</span>
        </div>

        <!-- Added Memories -->
        <div
          v-if="event.event.added_memories?.length"
          class="flex flex-col gap-2"
        >
          <div class="flex items-center gap-2 text-sm font-medium text-green-700 dark:text-green-400">
            <Icon
              name="lucide:plus-circle"
              class="size-4"
            />
            <span>{{ t('event.storeMemory.added') }} ({{ event.event.added_memories.length }})</span>
          </div>
          <div class="flex flex-col gap-2 pl-6">
            <div
              v-for="(memory, index) in event.event.added_memories"
              :key="`added-${index}`"
              class="flex items-start gap-2 text-sm"
            >
              <span class="text-green-600 dark:text-green-400">•</span>
              <span class="flex-1">{{ memory }}</span>
            </div>
          </div>
        </div>

        <!-- Updated Memories -->
        <div
          v-if="event.event.updated_memories?.length"
          class="flex flex-col gap-2"
        >
          <div class="flex items-center gap-2 text-sm font-medium text-blue-700 dark:text-blue-400">
            <Icon
              name="lucide:pencil"
              class="size-4"
            />
            <span>{{ t('event.storeMemory.updated') }} ({{ event.event.updated_memories.length }})</span>
          </div>
          <div class="flex flex-col gap-2 pl-6">
            <div
              v-for="(memory, index) in event.event.updated_memories"
              :key="`updated-${index}`"
              class="flex items-start gap-2 text-sm"
            >
              <span class="text-blue-600 dark:text-blue-400">•</span>
              <span class="flex-1">{{ memory }}</span>
            </div>
          </div>
        </div>

        <!-- Deleted Memories -->
        <div
          v-if="event.event.deleted_memories?.length"
          class="flex flex-col gap-2"
        >
          <div class="flex items-center gap-2 text-sm font-medium text-red-700 dark:text-red-400">
            <Icon
              name="lucide:trash-2"
              class="size-4"
            />
            <span>{{ t('event.storeMemory.deleted') }} ({{ event.event.deleted_memories.length }})</span>
          </div>
          <div class="flex flex-col gap-2 pl-6">
            <div
              v-for="(memory, index) in event.event.deleted_memories"
              :key="`deleted-${index}`"
              class="flex items-start gap-2 text-sm line-through opacity-60"
            >
              <span class="text-red-600 dark:text-red-400">•</span>
              <span class="flex-1">{{ memory }}</span>
            </div>
          </div>
        </div>
      </div>

      <div
        v-else
        class="text-sm text-surface-500 dark:text-surface-400"
      >
        {{ t('event.storeMemory.noChanges') }}
      </div>

      <!-- Relation Changes Graph -->
      <div
        v-if="hasRelationChanges"
        class="flex flex-col gap-3"
      >
        <div class="flex items-center gap-2 text-sm font-semibold text-surface-700 dark:text-surface-300">
          <Icon
            name="lucide:network"
            class="size-4"
          />
          <span>{{ t('event.storeMemory.relationChanges') }}</span>
        </div>

        <div class="flex flex-col gap-2 text-xs text-surface-600 dark:text-surface-400">
          <div
            v-if="event.event.added_relations?.length"
            class="flex items-center gap-2"
          >
            <Icon
              name="lucide:plus-circle"
              class="size-3 text-green-600 dark:text-green-400"
            />
            <span>{{ event.event.added_relations.length }} {{ t('event.storeMemory.addedRelations') }}</span>
          </div>
          <div
            v-if="event.event.deleted_relations?.length"
            class="flex items-center gap-2"
          >
            <Icon
              name="lucide:trash-2"
              class="size-3 text-red-600 dark:text-red-400"
            />
            <span>{{ event.event.deleted_relations.length }} {{ t('event.storeMemory.deletedRelations') }}</span>
          </div>
        </div>

        <div class="rounded-lg border border-surface-200 dark:border-surface-700">
          <MemoryGraph
            :relations="allRelations"
            :highlighted-relations="event.event.added_relations"
            height="300px"
          />
        </div>
      </div>
    </div>
  </EventDisplayBase>
</template>

<script setup lang="ts">
import { computed } from 'vue'

import type { BaseStoreMemoryEventReadable, ThreadDto, AgentEventReadable } from '@core/sdk/client'

const props = defineProps<{
  event: AgentEventReadable & { event: BaseStoreMemoryEventReadable }
  thread: ThreadDto
}>()

const { t } = useI18n()

const hasMemoryChanges = computed(() => {
  return (
    (props.event.event.added_memories?.length ?? 0) > 0
    || (props.event.event.updated_memories?.length ?? 0) > 0
    || (props.event.event.deleted_memories?.length ?? 0) > 0
  )
})

const hasRelationChanges = computed(() => {
  return (
    (props.event.event.added_relations?.length ?? 0) > 0
    || (props.event.event.deleted_relations?.length ?? 0) > 0
  )
})

const allRelations = computed(() => {
  return [
    ...(props.event.event.added_relations ?? []),
    ...(props.event.event.deleted_relations ?? []),
  ]
})
</script>
