<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="mage:file"
    is-external
  >
    <div class="flex flex-col gap-4">
      <div
        v-if="event.event.selected_namespaces.length > 0"
        class="flex flex-wrap items-center gap-2"
      >
        <span class="text-sm text-surface-600 dark:text-surface-400">
          {{ $t('event.rag_start.selected_namespaces') }}
        </span>
        <Tag
          v-for="(pair, index) in event.event.selected_namespaces"
          :key="index"
          :value="`${pair.bucket_name} / ${pair.namespace_name}`"
          severity="info"
        />
      </div>
      <div class="flex flex-col gap-8">
        <div
          v-for="(message, index) in event.event.messages"
          :key="index"
          class="flex flex-col gap-2"
        >
          <ChatMessage
            :message="message"
            :name="message.role === 'user' ? event.event.user.name : message.role"
            :email="message.role === 'user' ? event.event.user.email : ''"
            :date="new Date(event.event.created_at / 1_000_000)"
            :icon="agentIcon"
          />
        </div>
      </div>
    </div>
  </EventDisplayBase>
</template>

<script setup lang="ts">
// HeyAPI generates PascalCase types (RagStartEvent), but the runtime _event_name from Python's
// cls.__name__ is "RAGStartEvent". useEventComponent.ts maps against the runtime string;
// this import is the SDK type only. Do not "fix" one side without the other.
import type { ThreadDto, RagStartEvent, ContextualizedAgentEvent } from '@core/sdk/client'

const props = defineProps<{
  event: ContextualizedAgentEvent & { event: RagStartEvent }
  thread: ThreadDto
}>()

const agentIcon = useAgentIconFromThread(props.event, props.thread)
</script>
