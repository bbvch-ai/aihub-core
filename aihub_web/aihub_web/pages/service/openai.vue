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
    <NuxtPage />
  </div>
</template>

<script setup lang="ts">
import { onMounted, onBeforeUnmount } from 'vue'

const runtimeConfig = useRuntimeConfig()
const router = useRouter()
const localeRoute = useLocaleRoute()

const handleMessage = (event: MessageEvent) => {
  if (event.origin === runtimeConfig.public.webui.url) {
    const data = event.data

    // Check if it's the overlay command
    if (data.type === 'show-sources') {
      router.push(localeRoute(`/service/openai/${data.thread_id as string}`))
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
