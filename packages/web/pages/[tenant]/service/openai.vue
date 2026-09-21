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
const { setOpenWebUIContext, updateOpenWebUIContext, clearOpenWebUIContext } = useOpenWebUIContext()

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

const HANDLED_MESSAGE_TYPES = new Set([...Object.keys(VIEW_BY_ACTION), 'set-model-context', 'set-context'])

const openPanelView = (): string | null => {
  if (route.path.endsWith('/tracing')) return 'tracing'
  if (route.path.endsWith('/sources')) return 'sources'
  if (route.path.endsWith('/memories')) return 'memories'
  return null
}

// The action inside the iframe knows only the display, so the owning thread — the correct
// per-agent, salted one the pipe persisted events under — comes from the backend. Empty when no
// AI-Hub thread owns the display, which a plain-LLM message never does.
const resolveThreadId = async (displayId: string): Promise<string> => {
  try {
    const { thread_id } = await resolveThreadForDisplay({
      composable: '$fetch',
      path: { tenant_id: tenantId.value!, display_id: displayId },
    })
    return thread_id
  }
  catch (error) {
    console.warn('No AI-Hub thread found for display', displayId, error)
    return ''
  }
}

const handleMessage = async (event: MessageEvent) => {
  console.log('received post event', event)
  if (event.origin !== runtimeConfig.public.webui.url) return

  const data = event.data
  if (!HANDLED_MESSAGE_TYPES.has(data.type)) {
    console.log('Unknown message type:', data.type)
    return
  }

  const display_id = data.display_id as string
  if (!display_id) return

  // Explicit action-button click: open the requested side panel on the owning thread.
  const requestedView = VIEW_BY_ACTION[data.type]
  if (requestedView) {
    const thread_id = await resolveThreadId(display_id)
    // Leave the panel as-is rather than erroring when nothing owns the display.
    if (thread_id) {
      router.push(tenantPath(`/service/openai/${thread_id}/${display_id}/${requestedView}`))
    }
    return
  }

  // set-model-context: the inlet filter, which runs on every turn whatever routes it — including
  // a plain model, which reaches the API through OpenWebUI's own connection and no pipe at all.
  // It describes the turn from scratch, thread included, because a value it does not set is a
  // value the previous turn would otherwise lend to a report about this one.
  if (data.type === 'set-model-context') {
    setOpenWebUIContext({
      threadId: '',
      displayId: display_id,
      agentClass: (data.agent_class as string) ?? '',
      agentName: (data.agent_name as string) ?? '',
      model: (data.model as string) ?? '',
    })
    return
  }

  // set-context: the agent pipe, which alone knows the thread its events are persisted under.
  const thread_id = (data.thread_id as string) ?? ''
  updateOpenWebUIContext({ threadId: thread_id, displayId: display_id })

  // Keep an already-open panel synced. Only a resolved thread has a panel to sync to.
  if (!thread_id) return
  const view = openPanelView()
  if (view) {
    router.push(tenantPath(`/service/openai/${thread_id}/${display_id}/${view}`))
  }
}

// Set up event listener when component is mounted
onMounted(() => {
  window.addEventListener('message', handleMessage)
})

// Clean up event listener when component is unmounted
onBeforeUnmount(() => {
  window.removeEventListener('message', handleMessage)
  // The conversation is no longer on screen, so a report raised elsewhere must not claim it.
  clearOpenWebUIContext()
})
</script>
