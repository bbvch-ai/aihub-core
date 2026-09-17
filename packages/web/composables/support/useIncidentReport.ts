import type { IncidentContext } from './useIncidentContext'

// Browsers and form providers both truncate silently somewhere past 2000
// characters, and a half-delivered query string looks to the reporter like the
// form simply ignored the prefill. Staying under the limit is worth more than
// carrying every field, so these three are dropped — least useful first — until
// the URL fits. Everything dropped is something the reporter can still type.
const MAX_URL_LENGTH = 2000
const DROPPABLE_KEYS = ['browser', 'url', 'tenant_name'] as const

const PLACEHOLDER = /\{(\w+)\}/g

const render = (template: string, context: IncidentContext, omitted: Set<string>): string =>
  template.replace(PLACEHOLDER, (_match, key: string) => {
    if (omitted.has(key)) return ''
    const value = context[key as keyof IncidentContext]
    return value ? encodeURIComponent(value) : ''
  })

const buildFormUrl = (template: string, context: IncidentContext): string => {
  const omitted = new Set<string>()
  let url = render(template, context, omitted)
  for (const key of DROPPABLE_KEYS) {
    if (url.length <= MAX_URL_LENGTH) break
    omitted.add(key)
    url = render(template, context, omitted)
  }
  return url
}

// Opens the deployment's incident form with everything the platform already knows
// filled in. The form itself is hosted outside AI Hub and owned by whoever handles
// support for this deployment — the platform only contributes context and the
// consent step, which is why nothing here knows or cares who the provider is.
export const useIncidentReport = () => {
  const { t } = useI18n()
  const confirm = useConfirm()
  const config = useRuntimeConfig()
  const { buildIncidentContext } = useIncidentContext()

  const urlTemplate = computed(
    () => (config.public.incidentForm as { urlTemplate?: string } | undefined)?.urlTemplate ?? '',
  )

  const isAvailable = computed(() => Boolean(urlTemplate.value))

  function openForm(): void {
    if (!urlTemplate.value || !import.meta.client) return
    globalThis.open(
      buildFormUrl(urlTemplate.value, buildIncidentContext()),
      '_blank',
      'noopener,noreferrer',
    )
  }

  // The report leaves the platform for a third-party form, so the reporter is told
  // what travels with it before it does — not after.
  function requestReport(): void {
    if (!isAvailable.value) return
    confirm.require({
      header: t('support.consent_title'),
      message: t('support.consent_message'),
      icon: 'pi pi-external-link',
      rejectLabel: t('support.consent_cancel'),
      acceptLabel: t('support.consent_accept'),
      accept: openForm,
    })
  }

  return { isAvailable, requestReport }
}
