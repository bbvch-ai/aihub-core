import { getAgentThreads, type ThreadDto } from '@core/sdk/client'

export default defineQuery(() => {
  const route = useRoute()
  return useQuery<ThreadDto[]>({
    key: () => ['agent', route.params.agent_id, route.params.agent_class, 'threads'],
    staleTime: 1000 * 10, // 5 minutes
    enabled: true,
    query: async () => {
      return await getAgentThreads({
        composable: '$fetch',
        path: {
          agent_id: route.params.agent_id,
          agent_class: route.params.agent_class,
        },
      })
    },
  })
})
