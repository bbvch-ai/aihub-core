import { getChatDisclaimer } from '@core/sdk/client'

export const useChatDisclaimer = defineQuery(() => {
  const { tenantId } = useTenant()
  const { locale, t } = useI18n()
  const { data } = useQuery({
    key: () => ['tenant', tenantId.value ?? '', 'chat-disclaimer', locale.value],
    enabled: useTenantReady(),
    staleTime: 0,
    query: () => {
      const language = locale.value
      return getChatDisclaimer({
        composable: '$fetch',
        path: { tenant_id: tenantId.value! },
        onRequest: ({ options }) => {
          options.headers.set('lang', language)
        },
      })
    },
  })

  const disclaimer = computed(() => data.value ?? t('openwebui.default_disclaimer'))
  return { disclaimer }
})
