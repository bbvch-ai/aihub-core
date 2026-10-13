<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="mdi:file-eye-outline"
  >
    <dl class="grid grid-cols-[max-content_1fr] gap-x-4 gap-y-1 text-sm">
      <dt class="text-surface-500">
        {{ t('event.sandboxFileDisplayed.file') }}
      </dt>
      <dd class="break-all font-medium">
        {{ event.event.filename }}
      </dd>
      <dt class="text-surface-500">
        {{ t('event.sandboxFileDisplayed.type') }}
      </dt>
      <dd>{{ event.event.content_type }}</dd>
      <dt class="text-surface-500">
        {{ t('event.sandboxFileDisplayed.size') }}
      </dt>
      <dd>{{ size }}</dd>
      <dt class="text-surface-500">
        {{ t('event.sandboxFileDisplayed.path') }}
      </dt>
      <dd class="break-all font-mono text-xs">
        {{ event.event.path }}
      </dd>
    </dl>
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type { SandboxFileDisplayedEvent, ThreadDto, ContextualizedAgentEvent } from '@core/sdk/client'

const props = defineProps<{
  event: ContextualizedAgentEvent & { event: SandboxFileDisplayedEvent }
  thread: ThreadDto
}>()

const { t, n } = useI18n()

const size = computed<string>(() => {
  const bytes = props.event.event.size
  return bytes < 1024 ? `${bytes} B` : `${n(Math.round(bytes / 102.4) / 10)} KB`
})
</script>
