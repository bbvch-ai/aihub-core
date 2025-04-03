<template>
  <div class="flex flex-row">
    <div class="h-[calc(100vh-50px)] w-full">
      <iframe
        src="http://localhost:8080"
        width="100%"
        height="100%"
        title="Open Web UI"
      />
    </div>
    <Drawer
      v-model:visible="showSources"
      header="Sources"
      position="right"
      class="!w-[50vw]"
    >
      {{ activeThreadId }} / {{ activeDisplayId }}
      <EventList :events="eventsInThread" />
    </Drawer>
  </div>
</template>

<script setup lang="ts">
import { useEventsStore } from '@core/stores/useEventsStore'
import { ref, onMounted, onBeforeUnmount } from 'vue'

import type { WsServerEvent } from '@core/sdk/client'

// State for the overlay
const showSources = ref(false)
const sourceInfo = ref({})
const sourcesPannel = useTemplateRef<HTMLElement>('sources')

const { events } = storeToRefs(useEventsStore())
const activeThreadId = ref<string>('')
const activeDisplayId = ref<string>('')

const eventsInThread = computed<WsServerEvent[]>(() => {
  return events.value.filter((event) => {
    return event.thread_id === activeThreadId.value
      && (!activeDisplayId.value || event.display_id === activeDisplayId.value)
  })
})

onClickOutside(sourcesPannel, () => {
  showSources.value = false
})

// Function to handle incoming messages
const handleMessage = (event: MessageEvent) => {
  console.log('Received message:', event)
  // Since we're in development, the origin will be localhost
  // In production, you'd check for your app's actual domain
  if (event.origin === 'http://localhost:8080') {
    const data = event.data

    // Check if it's the overlay command
    if (data.type === 'show-sources') {
      activeThreadId.value = data.thread_id
      activeDisplayId.value = data.display_id
      showSources.value = !showSources.value
      sourceInfo.value = data
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
