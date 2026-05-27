// SPDX-License-Identifier: LicenseRef-Proprietary
import { deleteTenantMetadata as deleteTenantMetadataApi } from '~/sdk/client'

export const useDeleteTenantMetadata = defineMutation(() => {
  const queryCache = useQueryCache()

  const { mutateAsync: deleteTenantMetadataMutation } = useMutation({
    mutation: async ({ tenantId }: { tenantId: string }) => {
      await deleteTenantMetadataApi({
        composable: '$fetch',
        path: { tenant_id: tenantId },
      })
      queryCache.invalidateQueries({ key: ['admin-tenants'] })
      queryCache.invalidateQueries({ key: ['admin-tenants', 'unconfigured'] })
      queryCache.invalidateQueries({ key: ['my-tenants'] })
    },
  })
  return {
    deleteTenantMetadata: deleteTenantMetadataMutation,
  }
})
