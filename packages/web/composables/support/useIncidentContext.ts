import { format } from 'date-fns'

// Keys are snake_case because they are the placeholder names an operator writes
// into INCIDENT_FORM_URL_TEMPLATE, not internal identifiers.
export interface IncidentContext {
  tenant: string
  tenant_name: string
  version: string
  url: string
  date: string
  time: string
  user_name: string
  user_email: string
  browser: string
  thread_id: string
  display_id: string
  model: string
}

interface UserAgentBrand {
  brand: string
  version: string
}

interface UserAgentData {
  brands?: UserAgentBrand[]
  platform?: string
}

// "Chrome 129 · Windows" rather than the 120-character user-agent string: the
// whole context travels in a query string with a length budget, and a support
// engineer reads the short form faster anyway. Falls back to the raw UA on
// browsers without the (Chromium-only) hints API.
const describeBrowser = (): string => {
  if (!import.meta.client) return ''
  const data = (navigator as Navigator & { userAgentData?: UserAgentData }).userAgentData
  const brand = data?.brands?.find(candidate => !/not.?a.?brand/i.test(candidate.brand))
  if (brand) {
    return data?.platform ? `${brand.brand} ${brand.version} · ${data.platform}` : `${brand.brand} ${brand.version}`
  }
  return navigator.userAgent
}

// Everything the platform already knows about a report, so the reporter only has
// to describe what went wrong. Every field degrades to an empty string: the
// affordance is reachable from anonymous routes and from outside the chat, where
// tenant, user or conversation simply do not exist yet.
export const useIncidentContext = () => {
  const { tenantId } = useTenant()
  const { tenants } = useTenantMemberships()
  const { myUser } = useMyUser()
  const { versionDisplay } = useAppVersion()
  const { context: openWebUIContext } = useOpenWebUIContext()

  const tenantName = computed(
    () => tenants.value?.find(tenant => tenant.id === tenantId.value)?.name ?? '',
  )

  // Deliberately a snapshot rather than a computed: the reported time has to be
  // the moment the user raised the report, and a computed over a non-reactive
  // clock would freeze at whenever the page last rendered — hours earlier on a
  // tab left open, which is exactly the kind of tab a bug gets reported from.
  const buildIncidentContext = (): IncidentContext => {
    const now = new Date()
    return {
      tenant: tenantId.value ?? '',
      tenant_name: tenantName.value,
      version: versionDisplay.value ?? '',
      url: globalThis.location?.href ?? '',
      date: format(now, 'yyyy-MM-dd'),
      time: format(now, 'HH:mm'),
      user_name: myUser.value?.name ?? '',
      user_email: myUser.value?.email ?? '',
      browser: describeBrowser(),
      thread_id: openWebUIContext.value?.threadId ?? '',
      display_id: openWebUIContext.value?.displayId ?? '',
      model: openWebUIContext.value?.model ?? '',
    }
  }

  return { buildIncidentContext }
}
