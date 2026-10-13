<template>
  <div class="flex flex-col gap-3">
    <p class="text-sm font-semibold text-surface-600 dark:text-surface-400">
      {{ t('event.toolLoop.decidedCalls', { count: calls.length }) }}
    </p>
    <div
      v-for="call in calls"
      :key="call.id"
      class="flex flex-col gap-1 rounded-xl bg-surface-50 p-3 dark:bg-surface-850"
    >
      <div class="flex items-center gap-2">
        <Icon
          name="mynaui:tool"
          class="size-4"
        />
        <span class="font-semibold">{{ call.name }}</span>
        <span class="text-xs text-surface-500 dark:text-surface-400">{{ call.id }}</span>
      </div>
      <pre class="max-h-48 overflow-auto whitespace-pre-wrap break-words text-xs">{{ call.arguments }}</pre>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Message } from '@core/sdk/client'

const props = defineProps<{
  messages: Message[]
  toolCallIds: string[]
}>()

const { t } = useI18n()

type DecidedCall = { id: string, name: string, arguments: string }

const prettyArguments = (raw: unknown): string => {
  if (typeof raw !== 'string') {
    return JSON.stringify(raw ?? {}, null, 2)
  }
  try {
    return JSON.stringify(JSON.parse(raw), null, 2)
  }
  catch {
    return raw
  }
}

const calls = computed<DecidedCall[]>(() => {
  const wanted = new Set(props.toolCallIds)
  return props.messages
    .flatMap(message => message.tool_calls ?? [])
    .map((call) => {
      const fn = (call.function ?? {}) as { name?: string, arguments?: unknown }
      return { id: String(call.id ?? ''), name: fn.name ?? '', arguments: prettyArguments(fn.arguments) }
    })
    .filter(call => wanted.has(call.id))
})
</script>
