import { updateTenantSettings, type TenantSettingsDto } from '@core/sdk/client'

export const useUpdateTenantSettings = defineMutation(() => {
  const queryCache = useQueryCache()
  const { mutateAsync: saveSettings, isLoading: isSaving } = useMutation({
    mutation: async ({ tenantId, settings }: { tenantId: string, settings: TenantSettingsDto }) => {
      const saved = await updateTenantSettings({
        composable: '$fetch',
        path: { tenant_id: tenantId },
        body: settings,
      })
      queryCache.setQueryData(['tenant', tenantId, 'settings'], saved)
      await queryCache.invalidateQueries({ key: ['tenant', tenantId, 'chat-disclaimer'] }, false)
      return saved
    },
  })
  return { saveSettings, isSaving }
})
