import { getMyUsage, type UsageStatusDto } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'

export default defineQuery(() => {
  const {
    data: usage,
    isPending: usageIsLoading,
    refetch,
  } = useQuery<UsageStatusDto>({
    key: () => ['usage', 'me'],
    staleTime: minutesToMilliseconds(1),
    query: async () => {
      return await getMyUsage({
        composable: '$fetch',
      })
    },
  })
  return {
    usage,
    usageIsLoading,
    refetchUsage: refetch,
  }
})
