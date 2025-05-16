import { type DocumentDto, getDocumentById } from '@core/sdk/client'
import { useRoute } from 'vue-router'

export const useDocument = defineQuery(() => {
  const route = useRoute()
  const { data: document, isPending: documentIsLoading } = useQuery<DocumentDto>({
    key: () => ['knowledge', 'db', route.params.db as string, 'namespace', route.params.namespace as string, 'document', route.params.document_id as string],
    staleTime: 1000 * 60 * 5, // 5 minutes
    enabled: true,
    query: async () => {
      return await getDocumentById({
        composable: '$fetch',
        path: {
          db: route.params.db,
          namespace: route.params.namespace,
          document_id: route.params.document_id as string,
        },
      })
    },
  })
  return {
    document,
    documentIsLoading,
  }
})
