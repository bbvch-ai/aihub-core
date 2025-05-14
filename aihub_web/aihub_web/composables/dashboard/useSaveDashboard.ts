import { updateMyDashboardSettings } from '@core/sdk/client'

import type { GridStackOptions } from 'gridstack/dist/types'

export const useSaveDashboard = () => {
  const queryCache = useQueryCache()

  const { mutate: saveDashboard } = useMutation({
    mutation: async ({ grid }: { grid: GridStackOptions }) => {
      await updateMyDashboardSettings({
        composable: '$fetch',
        body: grid,
      })
      queryCache.invalidateQueries({ key: ['my_user'] })
    },
  })
  return {
    saveDashboard,
  }
}
