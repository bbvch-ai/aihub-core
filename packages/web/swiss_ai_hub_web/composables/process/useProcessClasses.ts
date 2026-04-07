import { type ProcessClassDtoReadable, getProcessClasses } from '@core/sdk/client'
import { useQuery } from '@pinia/colada'
import { minutesToMilliseconds } from 'date-fns'

export type ProcessClassDto = ProcessClassDtoReadable

export const useProcessClasses = defineQuery((options?: { online?: boolean }) => {
  const { tenantName } = useTenant()

  const { data: processClasses, isPending: processClassesAreLoading } = useQuery<ProcessClassDto[]>({
    key: () => ['process-classes', tenantName.value, options?.online],
    staleTime: minutesToMilliseconds(5),
    enabled: computed(() => !!tenantName.value),
    query: async () => {
      return await getProcessClasses({
        composable: '$fetch',
        path: { tenant_id: tenantName.value! },
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
