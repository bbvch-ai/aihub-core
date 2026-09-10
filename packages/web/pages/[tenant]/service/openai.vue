<template>
  <div class="flex flex-row">
    <div class="h-[calc(100vh-50px)] w-full">
      <iframe
        :src="`${runtimeConfig.public.webui.url}/oauth/oidc/login`"
        width="100%"
        height="100%"
        title="Open WebUI"
        allow="clipboard-write 'src'; clipboard-read 'src'; microphone 'src'; camera 'src'; display-capture 'src'; fullscreen 'src'; geolocation 'src'; autoplay 'src'"
        @load="handleIframeLoad"
      />
    </div>
    <NuxtPage />

    <Dialog
      v-model:visible="mismatchDetected"
      :header="t('tenant.mismatch_warning')"
      modal
      :closable="false"
    >
      <p>{{ t('tenant.mismatch_description', { tenant: backendTenantName }) }}</p>
      <template #footer>
        <Button
          :label="t('tenant.mismatch_switch_action')"
          icon="pi pi-refresh"
          @click="onSwitchToBackendTenant"
        />
      </template>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { resolveThreadForDisplay } from '@core/sdk/client'
import { onBeforeUnmount, onMounted } from 'vue'

const { t } = useI18n()
const runtimeConfig = useRuntimeConfig()
const route = useRoute()
const router = useRouter()
const tenantPath = useTenantPath()
const localePath = useLocalePath()
const { mismatchDetected, backendTenantId, backendTenantName } = useTenantPolling()
const { setTenant, tenantId } = useTenant()

async function onSwitchToBackendTenant() {
  if (!backendTenantId.value) return
  await setTenant(backendTenantId.value)
}

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

const VIEW_BY_ACTION: Record<string, string> = {
  'show-traces': 'tracing',
  'show-sources': 'sources',
  'show-memories': 'memories',
}

const openPanelView = (): string | null => {
  if (route.path.endsWith('/tracing')) return 'tracing'
  if (route.path.endsWith('/sources')) return 'sources'
  if (route.path.endsWith('/memories')) return 'memories'
  return null
}

const handleMessage = async (event: MessageEvent) => {
  console.log('received post event', event)
  if (event.origin !== runtimeConfig.public.webui.url) return

  const data = event.data
  if (!['show-traces', 'show-sources', 'show-memories', 'set-context'].includes(data.type)) {
    console.log('Unknown message type:', data.type)
    return
  }

  const display_id = data.display_id as string
  if (!display_id) return

  // Explicit action-button click: the action knows only the display, so resolve its owning thread from the backend
  // (the correct per-agent, salted thread the pipe persisted events under).
  const requestedView = VIEW_BY_ACTION[data.type]
  if (requestedView) {
    try {
      const { thread_id } = await resolveThreadForDisplay({
        composable: '$fetch',
        path: { tenant_id: tenantId.value!, display_id },
      })
      router.push(tenantPath(`/service/openai/${thread_id}/${display_id}/${requestedView}`))
    }
    catch (error) {
      // No AI-Hub thread owns this display (e.g. a plain-LLM message) — leave the panel as-is instead of erroring.
      console.warn('No AI-Hub thread found for display', display_id, error)
    }
    return
  }

  // set-context: the pipe pushes the correct thread_id as each message streams; keep an already-open panel synced.
  const view = openPanelView()
  if (view) {
    const thread_id = data.thread_id as string
    if (thread_id) {
      router.push(tenantPath(`/service/openai/${thread_id}/${display_id}/${view}`))
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
