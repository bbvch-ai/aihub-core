import { type DocumentDto, getDocumentById } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'
import { useRoute } from 'vue-router'

export const useDocument = defineQuery(() => {
  const route = useRoute()

  const database = computed(() => route.params.db as string)
  const namespace = computed(() => route.params.namespace as string)
  const documentId = computed(() => route.params.document_id as string)

  const { data: document, isPending: documentIsLoading } = useQuery<DocumentDto>({
    key: () => ['knowledge', 'databases', database.value, 'namespaces', namespace.value, 'documents', documentId.value],
    staleTime: minutesToMilliseconds(5),
    enabled: () => !!database.value && !!namespace.value && !!documentId.value,
    query: async () => {
      return await getDocumentById({
        composable: '$fetch',
        path: {
          database: database.value,
          namespace: namespace.value,
          document_id: documentId.value,
        },
      })
    },
  })
  return {
    document,
    documentIsLoading,
  }
})
