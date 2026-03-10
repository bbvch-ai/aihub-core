<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="mage:arrowlist"
  >
    <div class="flex flex-col gap-4">
      <IconField class="w-full">
        <InputIcon class="pi pi-search" />
        <InputText
          :model-value="event.event.query"
          class="w-full"
          readonly
        />
      </IconField>
      <div class="flex items-center gap-2 pt-5 text-sm font-medium text-surface-600 dark:text-surface-400">
        <Icon
          name="mage:filter"
          class="size-4"
        />
        <span>{{ t('event.reranker.topDocuments', { count: event.event.top_k }) }}</span>
      </div>
      <ChatSourceNodes
        :nodes="event.event.output_nodes ?? []"
      />
    </div>
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type { RerankerEvent, ThreadDto, ContextualizedAgentEvent } from '@core/sdk/client'

defineProps<{
  event: ContextualizedAgentEvent & { event: RerankerEvent }
  thread: ThreadDto
}>()

const { t } = useI18n()
</script>
