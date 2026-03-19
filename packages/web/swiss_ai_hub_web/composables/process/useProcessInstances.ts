import { type FullProcessInstanceDtoReadable, getAllProcessInstances } from '@core/sdk/client'
import { useQuery } from '@pinia/colada'
import { minutesToMilliseconds } from 'date-fns'

export type FullProcessInstanceDto = FullProcessInstanceDtoReadable

export const useProcessInstances = defineQuery((options?: { online?: boolean }) => {
  const { data: processInstances, isPending: processInstancesAreLoading } = useQuery<FullProcessInstanceDto[]>({
    key: () => ['process-instances', options?.online],
    staleTime: minutesToMilliseconds(5),
    enabled: true,
    query: async () => {
      return await getAllProcessInstances({
        composable: '$fetch',
        query: {
          online: options?.online,
        },
      })
    },
  })
  return {
    processInstances,
    processInstancesAreLoading,
  }
})
