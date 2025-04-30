<template>
  <div class="flex flex-row">
    <div class="h-[calc(100vh-50px)] w-full">
      <iframe
        :src="runtimeConfig.public.webui.url"
        width="100%"
        height="100%"
        title="Open Web UI"
      />
    </div>
    <Drawer
      v-model:visible="showSources"
      :header="thread?.name"
      position="right"
      class="!w-[50vw]"
    >
      <div class="flex flex-col gap-8">
        <div v-if="thread">
          <ThreadInfo
            :thread="thread"
          />
          <Divider />
          <div class="p-3">
            <EventList
              :events="eventsInThread"
              :thread="thread"
            />
          </div>
        </div>
      </div>
    </Drawer>
  </div>
</template>

<script setup lang="ts">
import { getThread, type ThreadDto, type WsServerEvent } from '@core/sdk/client'
import { useEventsStore } from '@core/stores/useEventsStore'
import { ref, onMounted, onBeforeUnmount } from 'vue'

const runtimeConfig = useRuntimeConfig()

// State for the overlay
const showSources = ref(false)
const sourcesPannel = useTemplateRef<HTMLElement>('sources')

const { events } = storeToRefs(useEventsStore())
const activeThreadId = ref<string>('')

const eventsInThread = computed<WsServerEvent[]>(() => {
  return events.value
    .filter((event) => {
      return event.thread_id === activeThreadId.value
    })
    .sort((a: WsServerEvent, b: WsServerEvent) => {
      return a.event.created_at - b.event.created_at
    })
})

const { data: thread } = useQuery<ThreadDto>({
  key: () => ['thread', activeThreadId.value],
  staleTime: 1000 * 10, // 5 minutes
  enabled: true,
  query: async () => {
    return await getThread({
      composable: '$fetch',
      path: { thread_id: activeThreadId.value },
    })
  },
})

onClickOutside(sourcesPannel, () => {
  showSources.value = false
})

// Function to handle incoming messages
const handleMessage = (event: MessageEvent) => {
  console.log('Received message:', event)
  // Since we're in development, the origin will be localhost
  // In production, you'd check for your app's actual domain
  if (event.origin === runtimeConfig.public.webui.url) {
    const data = event.data

    // Check if it's the overlay command
    if (data.type === 'show-sources') {
      activeThreadId.value = data.thread_id
      showSources.value = !showSources.value
    }
  }
}

// Set up event listener when component is mounted
onMounted(() => {
  window.addEventListener('message', handleMessage)
})

// Clean up event listener when component is unmounted
onBeforeUnmount(() => {
  window.removeEventListener('message', handleMessage)
})
</script>
