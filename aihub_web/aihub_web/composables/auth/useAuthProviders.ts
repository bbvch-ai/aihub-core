import { useQuery } from '@pinia/colada'
import { minutesToMilliseconds } from 'date-fns'

interface AuthProvider {
  alias: string
  display_name: string
  icon: string
}

export const useAuthProviders = defineQuery(() => {
  const { data: authProviders, isPending: isLoading } = useQuery<AuthProvider[]>({
    key: () => ['auth-providers'],
    staleTime: minutesToMilliseconds(5),
    query: async () => await $fetch<AuthProvider[]>('/api/v1/auth-providers/'),
  })

  return { authProviders, isLoading }
})
