<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="mdi:brain"
  >
    <div class="flex flex-col gap-6">
      <EventDisplayPartMessageList
        :messages="event.event.user_block ?? []"
        :event="event"
        :thread="thread"
        :title="t('event.capability.userMemories')"
      />
      <EventDisplayPartMessageList
        :messages="event.event.organization_block ?? []"
        :event="event"
        :thread="thread"
        :title="t('event.capability.organizationMemories')"
      />
    </div>
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type { ContextualizedAgentEvent, MemoryRecalledEvent, ThreadDto } from '@core/sdk/client'

defineProps<{
  event: ContextualizedAgentEvent & { event: MemoryRecalledEvent }
  thread: ThreadDto
}>()

const { t } = useI18n()
</script>
