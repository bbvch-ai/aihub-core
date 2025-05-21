import { type EvaluationDatasetResponseDto, listDatasetsEndpoint } from '@core/sdk/client'
import { useQuery } from '@pinia/colada'

export const useDatasets = defineQuery(() => {
  const { data: datasets, isPending: datasetsAreLoading } = useQuery<EvaluationDatasetResponseDto[]>({
    key: () => ['datasets'],
    staleTime: 1000 * 60 * 5, // 5 minutes
    enabled: true,
    query: async () => {
      return await listDatasetsEndpoint({
        composable: '$fetch',
      })
    },
  })
  return {
    datasets,
    datasetsAreLoading,
  }
})
