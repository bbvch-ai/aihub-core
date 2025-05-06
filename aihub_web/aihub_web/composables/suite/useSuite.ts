import { getSuite, type SuiteDto } from '@core/sdk/client'

export const useSuite = defineQuery(() => {
  const {
    data: suite,
    isPending: suiteIsLoading,
  } = useQuery<SuiteDto>({
    key: () => ['suite'],
    staleTime: 1000 * 60 * 5, // 5 minutes
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
