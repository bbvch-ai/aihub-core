import { type DocumentDto, getDocumentById } from '@core/sdk/client'
import { useRoute } from 'vue-router'

export const useDocument = defineQuery(() => {
  const route = useRoute()
  console.log(['namespace', route.params.namespace, 'documents', 'details', route.params.document_id as string])
  const { data: document, isPending: documentIsLoading } = useQuery<DocumentDto>({
    key: () => ['namespace', route.params.namespace, 'documents', 'details', route.params.document_id as string],
    staleTime: 1000 * 60 * 5, // 5 minutes
    enabled: true,
    query: async () => {
      return await getDocumentById({
        composable: '$fetch',
        path: {
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
