<template>
  <div class="flex flex-row">
    <div class="w-full h-[calc(100vh-50px)]">
      <iframe
        src="http://localhost:5173"
        width="100%"
        height="100%"
        title="Open Web UI"
      />
    </div>
    <div
      ref="sources"
      class="w-0 overflow-y-hidden transition-all"
      :class="{ 'w-1/3': showSources }"
    >
      <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.</p>
      <pre>
        {{ sourceInfo }}
      </pre>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'

// State for the overlay
const showSources = ref(false)
const sourceInfo = ref({})
const sourcesPannel = useTemplateRef<HTMLElement>('sources')

onClickOutside(sourcesPannel, () => {
  showSources.value = false
})

// Function to handle incoming messages
const handleMessage = (event: MessageEvent) => {
  console.log('Received message:', event)
  // Since we're in development, the origin will be localhost
  // In production, you'd check for your app's actual domain
  if (event.origin === 'http://localhost:5173') {
    const data = event.data

    // Check if it's the overlay command
    if (data.type === 'show-sources') {
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
