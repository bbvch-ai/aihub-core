import { getMyActiveTenant } from '@core/sdk/client'
import { useIntervalFn } from '@vueuse/core'

/**
 * Polls the backend active tenant every 30 seconds and detects mismatches
 * with the current URL tenant. Used exclusively on the OpenWebUI page where
 * the iframe relies on the backend's active tenant.
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

  return { mismatchDetected, backendTenantId, backendTenantName }
}
