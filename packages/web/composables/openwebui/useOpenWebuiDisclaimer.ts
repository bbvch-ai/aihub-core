import type { Ref } from 'vue'

export function useOpenWebuiDisclaimer(iframe: Ref<HTMLIFrameElement | null>, text: Ref<string>) {
  const config = useRuntimeConfig()
  const origin = new URL(config.public.webui.url).origin
  const type = 'aihub:chat-disclaimer'

  function sendDisclaimer() {
    iframe.value?.contentWindow?.postMessage({ type, version: 1, text: text.value }, origin)
  }

  function onMessage(event: MessageEvent) {
    if (event.origin !== origin || event.source !== iframe.value?.contentWindow) return
    if (event.data?.type === `${type}:ready` && event.data.version === 1) sendDisclaimer()
  }

  watch(text, sendDisclaimer)
  onMounted(() => window.addEventListener('message', onMessage))
  onBeforeUnmount(() => window.removeEventListener('message', onMessage))

  return { sendDisclaimer }
}
