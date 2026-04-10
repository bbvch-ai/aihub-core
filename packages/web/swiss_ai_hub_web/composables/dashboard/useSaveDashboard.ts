import { updateMyDashboard } from '@core/sdk/client'

import type { GridStackOptions } from 'gridstack/dist/types'

export const useSaveDashboard = () => {
  const queryCache = useQueryCache()

  const { mutate: saveDashboard } = useMutation({
    mutation: async ({ grid, tenantId }: { grid: GridStackOptions, tenantId: string }) => {
      await updateMyDashboard({
        composable: '$fetch',
        path: { tenant_id: tenantId },
        body: grid,
      })
      queryCache.invalidateQueries({ key: ['tenant', tenantId, 'my_user'] })
    },
  })
  return {
    saveDashboard,
  }
}
