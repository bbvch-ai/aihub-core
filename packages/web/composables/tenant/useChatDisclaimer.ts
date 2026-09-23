import { getChatDisclaimer } from '@core/sdk/client'

export const useChatDisclaimer = defineQuery(() => {
  const { tenantId } = useTenant()
  const { locale, t } = useI18n()
  const { data } = useQuery({
    key: () => ['tenant', tenantId.value ?? '', 'chat-disclaimer', locale.value],
    enabled: useTenantReady(),
    staleTime: 0,
    query: () => getChatDisclaimer({
      composable: '$fetch',
      path: { tenant_id: tenantId.value! },
      headers: { lang: locale.value },
    }),
  })

  const disclaimer = computed(() => data.value ?? t('tenant_settings.default_disclaimer'))
  return { disclaimer }
})
