import { getSupportedFileTypes } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'

export const useSupportedFileTypes = defineQuery(() => {
  const { data: supportedFileTypes } = useQuery<string[]>({
    key: () => ['supportedFileTypes'],
    staleTime: minutesToMilliseconds(60),
    enabled: true,
    query: async () => {
      return await getSupportedFileTypes({
        composable: '$fetch',
      })
    },
  })

  return {
    supportedFileTypes,
  }
})
