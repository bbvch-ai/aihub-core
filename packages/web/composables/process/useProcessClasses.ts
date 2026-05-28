import { type ProcessClassDtoReadable, getProcessClasses } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'

export type ProcessClassDto = ProcessClassDtoReadable

export const useProcessClasses = defineQuery((options?: { online?: boolean }) => {
  const { tenantId } = useTenant()

  const { data: processClasses, isPending: processClassesAreLoading } = useQuery<ProcessClassDto[]>({
    key: () => ['tenant', tenantId.value, 'process-classes', options?.online],
    staleTime: minutesToMilliseconds(5),
    enabled: useTenantReady(),
    query: async () => {
      return await getProcessClasses({
        composable: '$fetch',
        path: { tenant_id: tenantId.value! },
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
