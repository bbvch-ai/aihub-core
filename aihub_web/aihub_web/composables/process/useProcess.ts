import { type ProcessDto, getProcess } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'
import { useRoute } from 'vue-router'

export const useProcess = defineQuery(() => {
  const route = useRoute()
  const isRouteReady = useRouteReady('process_id', 'process_class')

  const { data: process, isPending: processIsLoading } = useQuery<ProcessDto>({
    key: () => ['processes', route.params.process_class as string, route.params.process_id as string],
    staleTime: minutesToMilliseconds(5),
    enabled: isRouteReady,
    query: async () => {
      return await getProcess({
        composable: '$fetch',
        path: {
          process_id: route.params.process_id as string,
          process_class: route.params.process_class as string,
        },
      })
    },
  })
  return {
    process,
    processIsLoading,
  }
})
