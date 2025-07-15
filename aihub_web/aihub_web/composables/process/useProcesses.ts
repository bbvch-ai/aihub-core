import { type ProcessDto, getProcesses } from '@core/sdk/client'
import { useQuery } from '@pinia/colada'
import { minutesToMilliseconds } from 'date-fns'

export const useProcesses = defineQuery(() => {
  const { data: processes, isPending: processesAreLoading } = useQuery<ProcessDto[]>({
    key: () => ['processes'],
    staleTime: minutesToMilliseconds(5),
    enabled: true,
    query: async () => {
      return await getProcesses({
        composable: '$fetch',
      })
    },
  })
  return {
    processes,
    processesAreLoading,
  }
})
