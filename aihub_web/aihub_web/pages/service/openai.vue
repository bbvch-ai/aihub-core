<template>
  <div class="flex flex-row">
    <div class="h-[calc(100vh-50px)] w-full">
      <iframe
        :src="`${runtimeConfig.public.webui.url}/oauth/oidc/login`"
        width="100%"
        height="100%"
        title="Open WebUI"
        allow="microphone"
        @load="handleIframeLoad"
      />
    </div>
    <NuxtPage />
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted } from 'vue'

const runtimeConfig = useRuntimeConfig()
const route = useRoute()
const router = useRouter()
const localeRoute = useLocaleRoute()
const localePath = useLocalePath()

let initialLoadDone = false

const handleIframeLoad = () => {
  // Skip the initial load when iframe first renders OpenWebUI
  if (!initialLoadDone) {
    initialLoadDone = true
    return
  }

  // Subsequent loads mean the iframe navigated (e.g. Keycloak logout redirect).
  // Redirect to home without destroying the parent session — the local JWT
  // stays valid, so the rest of the app keeps working. When the user navigates
  // back here, the iframe re-triggers OIDC login against Keycloak.
  console.log('OpenWebUI iframe navigated away, redirecting to home')
  router.push(localePath('/'))
}

const handleMessage = (event: MessageEvent) => {
  console.log('received post event', event)
  if (event.origin === runtimeConfig.public.webui.url) {
    const data = event.data

    if (!['show-traces', 'show-sources', 'show-memories', 'set-context'].includes(data.type)) {
      console.log('Unknown message type:', data.type)
      return
    }

    const thread_id = data.thread_id as string
    const display_id = data.display_id as string

    if (data.type === 'show-traces' || route.path.endsWith('/tracing')) {
      router.push(localeRoute(`/service/openai/${thread_id}/${display_id}/tracing`))
    }
    if (data.type === 'show-sources' || route.path.endsWith('/sources')) {
      router.push(localeRoute(`/service/openai/${thread_id}/${display_id}/sources`))
    }
    if (data.type === 'show-memories' || route.path.endsWith('/memories')) {
      router.push(localeRoute(`/service/openai/${thread_id}/${display_id}/memories`))
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
