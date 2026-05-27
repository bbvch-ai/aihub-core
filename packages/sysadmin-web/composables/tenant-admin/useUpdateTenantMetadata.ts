// SPDX-License-Identifier: LicenseRef-Proprietary
import { updateTenantMetadata as updateTenantMetadataApi, type UpdateTenantMetadataRequest } from '~/sdk/client'

export const useUpdateTenantMetadata = defineMutation(() => {
  const queryCache = useQueryCache()

  const { mutateAsync: updateTenantMetadataMutation } = useMutation({
    mutation: async ({ tenantId, data }: { tenantId: string, data: UpdateTenantMetadataRequest }) => {
      await updateTenantMetadataApi({
        composable: '$fetch',
        path: { tenant_id: tenantId },
        body: data,
      })
      queryCache.invalidateQueries({ key: ['admin-tenants'] })
      queryCache.invalidateQueries({ key: ['my-tenants'] })
    },
  })
  return {
    updateTenantMetadata: updateTenantMetadataMutation,
  }
})
