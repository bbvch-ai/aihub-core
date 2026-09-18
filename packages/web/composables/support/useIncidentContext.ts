import { format } from 'date-fns'

interface UserAgentBrand {
  brand: string
  version: string
}

interface UserAgentData {
  brands?: UserAgentBrand[]
  platform?: string
}

// "Chrome 129 · Windows" rather than the 120-character user-agent string: a support engineer
// reads the short form faster, and the raw string tells them nothing extra. Falls back to the
// full agent on browsers without the (Chromium-only) hints API.
const describeBrowser = (): string => {
  if (!import.meta.client) return ''
  const data = (navigator as Navigator & { userAgentData?: UserAgentData }).userAgentData
  const brand = data?.brands?.find(candidate => !/not.?a.?brand/i.test(candidate.brand))
  if (!brand) return navigator.userAgent
  return data?.platform ? `${brand.brand} ${brand.version} · ${data.platform}` : `${brand.brand} ${brand.version}`
}

// The half of the report context only the browser knows. Its counterpart is filled server-side
// from the caller's token — tenant and reporter identity — because those are the two the
// reporter must not be able to get wrong by accident.
//
// Every key here is a question `id` in packages/core/.../incident/incident_form.yml. That naming
// is the whole contract: a key with no matching question is silently dropped.
export const useIncidentContext = () => {
  const { versionDisplay } = useAppVersion()
  const { context: openWebUIContext } = useOpenWebUIContext()

  // Deliberately a snapshot rather than a computed: the reported time has to be the moment the
  // reporter raised the report, and a computed over a non-reactive clock would freeze at whenever
  // the page last rendered — hours earlier on a tab left open, which is exactly the kind of tab a
  // bug gets reported from.
  const buildIncidentContext = (): Record<string, string> => ({
    occurred_at: format(new Date(), 'yyyy-MM-dd HH:mm'),
    version: versionDisplay.value ?? '',
    page_url: globalThis.location?.href ?? '',
    browser: describeBrowser(),
    conversation_id: openWebUIContext.value?.threadId ?? '',
    model: openWebUIContext.value?.model ?? '',
  })

  return { buildIncidentContext }
}
