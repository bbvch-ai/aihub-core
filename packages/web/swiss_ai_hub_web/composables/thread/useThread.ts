import { getThread, type ThreadDto } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'
import { useRoute } from 'vue-router'

export const useThread = defineQuery(() => {
  const route = useRoute()
  const { tenantId } = useTenant()

  const { data: thread, isPending: threadIsLoading } = useQuery<ThreadDto>({
    key: () => ['tenant', tenantId.value, 'threads', route.params.thread_id as string],
    staleTime: minutesToMilliseconds(5),
    enabled: useTenantReady('thread_id'),
    query: async () => {
      return await getThread({
        composable: '$fetch',
        path: {
          tenant_id: tenantId.value!,
          thread_id: route.params.thread_id as string,
        },
      })
    },
  })
  return {
    thread,
    threadIsLoading,
  }
})
