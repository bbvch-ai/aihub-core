import { client } from '@core/sdk/client/client.gen'

export const useUpdateMyLocale = defineMutation(() => {
  const { tenantId } = useTenant()
  const { mutateAsync } = useMutation({
    mutation: async ({ locale }: { locale: string }) => {
      await client.put({
        composable: '$fetch',
        url: '/{tenant_id}/my-account/locale',
        path: { tenant_id: tenantId.value! },
        body: { locale },
        headers: { 'Content-Type': 'application/json' },
      })
    },
  })
  return { updateMyLocale: mutateAsync }
})
