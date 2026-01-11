<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="vscode-icons:file-type-document"
  >
    <div class="flex flex-col gap-2">
      <div class="flex items-center gap-2">
        <Badge
          :value="event.event.operation"
          :severity="event.event.operation === 'created' ? 'success' : 'info'"
        />
        <code class="rounded bg-surface-100 px-2 py-1 text-sm dark:bg-surface-700">
          {{ event.event.path }}
        </code>
      </div>
      <div
        v-if="event.event.content_preview"
        class="border-l-4 border-surface-200 pl-3 dark:border-surface-600"
      >
        <p class="font-mono text-sm text-surface-600 dark:text-surface-400">
          {{ event.event.content_preview }}
        </p>
      </div>
      <div
        v-if="event.event.mime_type"
        class="text-xs text-surface-500"
      >
        {{ event.event.mime_type }}
      </div>
    </div>
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type { DocumentChangedEventReadable, ThreadDto, AgentEventReadable } from '@core/sdk/client'

defineProps<{
  event: AgentEventReadable & { event: DocumentChangedEventReadable }
  thread: ThreadDto
}>()
</script>
