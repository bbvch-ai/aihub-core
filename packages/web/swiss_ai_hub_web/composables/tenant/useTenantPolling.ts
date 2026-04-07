import { getMyActiveTenant } from '@core/sdk/client'

/**
 * Polls the backend active tenant every 30 seconds and detects mismatches
 * with the current URL tenant. Used exclusively on the OpenWebUI page where
 * the iframe relies on the backend's active tenant.
 */
export function useTenantPolling() {
  const { tenantName } = useTenantFromRoute()
  const mismatchDetected = ref(false)
  const backendTenantName = ref<string | undefined>()

  let interval: ReturnType<typeof setInterval> | undefined

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

  onMounted(() => {
    poll()
    interval = setInterval(poll, 30_000)
  })

  onUnmounted(() => {
    if (interval) clearInterval(interval)
  })

  return { mismatchDetected, backendTenantName }
}
