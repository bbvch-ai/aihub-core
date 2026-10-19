import { getMyActiveTenant } from '@core/sdk/client'
import { useDocumentVisibility, useEventListener, useIntervalFn } from '@vueuse/core'

/**
 * Polls the backend active tenant and detects mismatches with the current URL
 * tenant. Used exclusively on the OpenWebUI page where the iframe relies on the
 * backend's active tenant. The pipe resolves that tenant per request, so a tab
 * whose tenant was switched elsewhere must notice before its next message: it
 * re-checks when it becomes visible and when another tab of this browser
 * switches. The interval covers switches on other devices.
 */
export function useTenantPolling() {
  const { tenantId } = useTenant()
  const mismatchDetected = ref(false)
  const backendTenantId = ref<string | undefined>()
  const backendTenantName = ref<string | undefined>()

  async function poll() {
    try {
      const activeTenant = await getMyActiveTenant({ composable: '$fetch' })
      backendTenantId.value = activeTenant?.id
      backendTenantName.value = activeTenant?.name
      mismatchDetected.value = !!(tenantId.value && activeTenant?.id && tenantId.value !== activeTenant.id)
    }
    catch {
      // Ignore polling errors
    }
  }

  useIntervalFn(poll, 30_000, { immediateCallback: true })

  const visibility = useDocumentVisibility()
  watch(visibility, (visibilityState: DocumentVisibilityState) => {
    if (visibilityState === 'visible') void poll()
  })

  const channel = new BroadcastChannel(ACTIVE_TENANT_CHANNEL)
  useEventListener(channel, 'message', poll)
  onScopeDispose(() => channel.close())

  return { mismatchDetected, backendTenantId, backendTenantName, refresh: poll }
}
