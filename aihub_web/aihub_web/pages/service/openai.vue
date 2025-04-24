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
          <EventList
            :events="eventsInDisplay"
            :thread="thread"
          />
          <Paginator
            v-model:first="page"
            always-show
            :rows="1"
            :total-records="uniqueDisplayIds.length"
          />
        </div>
      </div>
    </Drawer>
  </div>
</template>

<script setup lang="ts">
import { getThread, type ThreadResponse, type WsServerEvent } from '@core/sdk/client'
import { useEventsStore } from '@core/stores/useEventsStore'
import { ref, onMounted, onBeforeUnmount } from 'vue'

const runtimeConfig = useRuntimeConfig()

// State for the overlay
const showSources = ref(false)
const sourceInfo = ref({})
const sourcesPannel = useTemplateRef<HTMLElement>('sources')

const { events } = storeToRefs(useEventsStore())
const activeThreadId = ref<string>('')
const activeDisplayId = ref<string>('')
const page = ref<number>(0)

const eventsInThread = computed<WsServerEvent[]>(() => {
  return events.value
    .filter((event) => {
      return event.thread_id === activeThreadId.value
    })
    .sort((a: WsServerEvent, b: WsServerEvent) => {
      return a.event.created_at - b.event.created_at
    })
})

const uniqueDisplayIds = computed<string[]>(() => {
  const displayIds: string[] = []
  eventsInThread.value.forEach((event: WsServerEvent) => {
    if (event.display_id && !displayIds.includes(event.display_id)) {
      displayIds.push(event.display_id)
    }
  })
  return displayIds
})

const eventsInDisplay = computed<WsServerEvent[]>(() => {
  const selectedDisplay = uniqueDisplayIds.value[page.value]
  return eventsInThread.value.filter((event) => {
    return event.display_id === selectedDisplay
  })
})

const { data: thread } = useQuery<ThreadResponse>({
  key: () => ['thread', activeThreadId.value],
  staleTime: 1000 * 10, // 5 minutes
  enabled: true,
  query: async () => {
    console.log('Fetching thread2', activeThreadId.value)
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
      activeDisplayId.value = data.display_id
      showSources.value = !showSources.value
      sourceInfo.value = data

      nextTick(() => {
        page.value = uniqueDisplayIds.value.length - 1
      })
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
