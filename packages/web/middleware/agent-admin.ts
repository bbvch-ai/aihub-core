import { getSuite } from '@core/sdk/client'

const AGENT_SERVICE_PATH = '/service/agents'

// Hiding the app from the navigation is not access control: the management pages stay reachable by URL.
// Admission is decided by the same /suites answer the navigation is built from, so the page and the app
// list can never disagree about who is an agent admin.
export default defineNuxtRouteMiddleware(async (to) => {
  const tenantId = to.params.tenant as string | undefined
  if (!tenantId) return

  const { $i18n } = useNuxtApp()

  let isAgentAdmin = false
  try {
    const suite = await getSuite({ composable: '$fetch', path: { tenant_id: tenantId } })
    isAgentAdmin = suite.services.some(service => service.path === AGENT_SERVICE_PATH)
  }
  catch (error) {
    // Fail closed — an unreadable suite is not a licence to open the management surface.
    console.error('agent-admin middleware: failed to read the suite', error)
  }

  if (!isAgentAdmin) {
    return abortNavigation(createError({
      statusCode: 403,
      statusMessage: $i18n.t('http_error.code.403'),
      fatal: true,
    }))
  }
})
