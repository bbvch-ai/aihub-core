import type { Ref } from 'vue'

export function useOpenWebuiMods(iframe: Ref<HTMLIFrameElement | null>, tenantId: Ref<string | null>, webuiUrl: string) {
  const origin = new URL(webuiUrl).origin
  const { locale, t } = useI18n()
  const toast = useToast()
  const type = 'aihub:mods'
  const group = 'openwebui-mods-update'
  const notice = ref<'changed' | 'failed' | null>(null)

  function clearModNotice() {
    notice.value = null
    toast.removeGroup(group)
  }

  function showNotice() {
    toast.removeGroup(group)
    if (!notice.value) return
    toast.add({
      group,
      severity: notice.value === 'changed' ? 'info' : 'warn',
      summary: t(`openwebui.mods.${notice.value}_title`),
      detail: t(`openwebui.mods.${notice.value}_detail`),
    })
  }

  function sendModContext() {
    iframe.value?.contentWindow?.postMessage({ type, version: 1, tenantId: tenantId.value, locale: locale.value }, origin)
  }

  function onMessage(event: MessageEvent) {
    if (event.origin !== origin || event.source !== iframe.value?.contentWindow) return
    const data = event.data
    if (data?.version !== 1) return
    if (data.type === `${type}:ready`) {
      clearModNotice()
      sendModContext()
      return
    }
    if (data.type !== `${type}:update`) return
    if (data.tenantId === null && data.reason === null) {
      clearModNotice()
      return
    }
    if (data.tenantId !== tenantId.value || !/^[a-f0-9]{32}$/.test(data.viewId)) return
    if (data.reason !== null && data.reason !== 'changed' && data.reason !== 'failed') return
    if (notice.value === data.reason) return
    notice.value = data.reason
    showNotice()
  }

  watch([tenantId, locale], sendModContext, { flush: 'sync' })
  watch(tenantId, clearModNotice, { flush: 'sync' })
  watch(locale, showNotice)
  onMounted(() => window.addEventListener('message', onMessage))
  onBeforeUnmount(() => {
    iframe.value?.contentWindow?.postMessage({ type, version: 1, tenantId: null }, origin)
    window.removeEventListener('message', onMessage)
    clearModNotice()
  })

  return { sendModContext, clearModNotice }
}
