import { type Namespace, getNamespaces } from '@core/sdk/client'
import { useRoute } from 'vue-router'

export const useNamespaces = defineQuery(() => {
  const route = useRoute()
  const { data: namespaces, isPending: namespacesAreLoading } = useQuery<Namespace[]>({
    key: () => ['namespace', route.params.namespace, 'documents', route.params.document_id as string],
    staleTime: 1000 * 60 * 5, // 5 minutes
    enabled: true,
    query: async () => {
      return await getNamespaces({
        composable: '$fetch',
      })
    },
  })
  return {
    namespaces,
    namespacesAreLoading,
  }
})
