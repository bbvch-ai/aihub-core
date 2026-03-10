import { type ProcessClassDtoReadable, getProcessClasses } from '@core/sdk/client'
import { useQuery } from '@pinia/colada'
import { minutesToMilliseconds } from 'date-fns'

export type ProcessClassDto = ProcessClassDtoReadable

export const useProcessClasses = defineQuery((options?: { online?: boolean }) => {
  const { data: processClasses, isPending: processClassesAreLoading } = useQuery<ProcessClassDto[]>({
    key: () => ['process-classes', options?.online],
    staleTime: minutesToMilliseconds(5),
    enabled: true,
    query: async () => {
      return await getProcessClasses({
        composable: '$fetch',
        query: {
          online: options?.online,
        },
      })
    },
  })
  return {
    processClasses,
    processClassesAreLoading,
  }
})
