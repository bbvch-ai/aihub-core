import { updateMyLocale } from '@core/sdk/client'

export const useUpdateMyLocale = defineMutation(() => {
  const { tenantId } = useTenant()

  const { mutateAsync, isLoading } = useMutation({
    mutation: async ({ locale }: { locale: string }) => {
      await updateMyLocale({
        composable: '$fetch',
        path: { tenant_id: tenantId.value! },
        body: { locale },
      })
    },
  })

  return {
    updateMyLocale: mutateAsync,
    updateMyLocaleIsLoading: isLoading,
  }
})
