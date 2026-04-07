import { getMyActiveTenant } from '@core/sdk/client'
import { useIntervalFn } from '@vueuse/core'

/**
 * Polls the backend active tenant every 30 seconds and detects mismatches
 * with the current URL tenant. Used exclusively on the OpenWebUI page where
 * the iframe relies on the backend's active tenant.
 */
export function useTenantPolling() {
  const { tenantName } = useTenant()
  const mismatchDetected = ref(false)
  const backendTenantName = ref<string | undefined>()

  async function poll() {
    try {
      const activeTenant = await getMyActiveTenant({ composable: '$fetch' })
      backendTenantName.value = activeTenant?.name
      mismatchDetected.value = !!(tenantName.value && activeTenant?.name && tenantName.value !== activeTenant.name)
    }
    catch {
      // Ignore polling errors
    }
  }

  useIntervalFn(poll, 30_000, { immediateCallback: true })

  return { mismatchDetected, backendTenantName }
}
