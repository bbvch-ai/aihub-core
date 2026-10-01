import type { ToastServiceMethods } from 'primevue/toastservice'

// When the `api` container is not running, Traefik drops its router
// (Host && PathPrefix('/api/v1'), priority 6000) and `/api/v1/...` falls through
// to `web-default` (bare Host, priority 100) — the SPA nginx, whose
// `try_files $uri /index.html` answers 200 text/html. ofetch resolves that to
// responseType "text", so `_data` is the index.html source string with status
// 200 and no error, and Pinia-Colada caches it as a valid DTO. Consumers then
// read a list off it and throw inside a computed, taking the layout down.
//
// Deliberately a text/html DENYLIST rather than a JSON allowlist: the SDK
// generator never emits `responseType`, so createSpeech (audio/*),
// createTranscription (text/plain) and streaming chat completions
// (text/event-stream) are indistinguishable from an unannotated JSON call.
// Requiring JSON would break all three. No AI-Hub endpoint answers text/html.
const HTML_CONTENT_TYPE = /^text\/html\b/i

// Every in-flight query fails at once when the API is unreachable. One toast is
// a diagnosis, a dozen is noise. Module scope so both SDK clients share it.
const NOTIFY_THROTTLE_MS = 10_000

let lastNotifiedAt = 0

// Structural supertype of ofetch's hook context — `ofetch` itself is not
// resolvable from packages/web under pnpm's isolated linker.
type ApiResponseContext = {
  options: { responseType?: string }
  response: Response
}

// Only what the notifier reads. Structural on purpose: defineNuxtPlugin hands
// its callback `_NuxtApp` while useNuxtApp() returns `NuxtApp`, and both call
// sites satisfy this.
type NotifyCapableApp = {
  vueApp: { config: { globalProperties: Record<string, unknown> } }
  $i18n?: unknown
}

export class HtmlResponseError extends Error {
  readonly status: number
  readonly contentType: string
  readonly url: string

  constructor(response: Response, contentType: string) {
    super(
      `Expected JSON from the AI-Hub API but received ${contentType} (HTTP ${response.status}, ${response.url}). `
      + 'The API is most likely unreachable and a proxy answered with the SPA shell.',
    )
    this.name = 'HtmlResponseError'
    this.status = response.status
    this.contentType = contentType
    this.url = response.url
  }
}

const notifyApiUnavailable = (nuxtApp: NotifyCapableApp): void => {
  const now = Date.now()
  if (now - lastNotifiedAt < NOTIFY_THROTTLE_MS) return

  // `useToast()` injects and needs a component instance, which an ofetch hook
  // does not have. Read lazily so plugin ordering cannot matter.
  const toast = nuxtApp.vueApp.config.globalProperties.$toast as ToastServiceMethods | undefined
  if (!toast) return

  lastNotifiedAt = now
  const i18n = nuxtApp.$i18n as { t?: (key: string) => string } | undefined
  toast.add({
    severity: 'error',
    summary: i18n?.t?.('http_error.code.503') ?? 'Our service is temporarily unavailable.',
    life: 10_000,
  })
}

// `nuxtApp` is captured rather than resolved inside the hook: useNuxtApp()
// throws once Nuxt's async context is gone, which it is by response time.
export const createHtmlResponseGuard = (nuxtApp: NotifyCapableApp) => {
  return ({ options, response }: ApiResponseContext): void => {
    // A caller that asked for a non-JSON body knows what it is doing.
    if (options.responseType && options.responseType !== 'json') return

    // 4xx/5xx still reject through ofetch and reach onResponseError, which owns
    // the localized toast. This hook runs BEFORE ofetch's `status >= 400`
    // branch, so throwing here would mask a correct "404" with a generic error.
    if (!response.ok) return

    // An absent content-type (202 with an empty body) fails this test and is
    // left alone; ofetch skips 204 bodies entirely.
    const contentType = response.headers.get('content-type') ?? ''
    if (!HTML_CONTENT_TYPE.test(contentType)) return

    notifyApiUnavailable(nuxtApp)

    // Must throw: ofetch ignores this hook's return value, so returning would
    // leave the HTML string in `_data` for Pinia-Colada to cache as valid data.
    throw new HtmlResponseError(response, contentType)
  }
}
