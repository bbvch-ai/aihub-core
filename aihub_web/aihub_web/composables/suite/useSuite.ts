import { getSuite, type SuiteDto } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'

export const useSuite = defineQuery(() => {
  const {
    data: suite,
    isPending: suiteIsLoading,
  } = useQuery<SuiteDto>({
    key: () => ['suite'],
    staleTime: minutesToMilliseconds(5),
    enabled: true,
    query: async () => {
      return await getSuite({
        composable: '$fetch',
      })
    },
  })

  return {
    suite,
    suiteIsLoading,
  }
})
