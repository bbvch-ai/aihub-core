interface AuthProvider {
  alias: string
  display_name: string
  icon: string
}

export const useAuthProviders = () => {
  const authProviders = ref<AuthProvider[]>([])
  const isLoading = ref(true)

  const fetchAuthProviders = async () => {
    isLoading.value = true
    try {
      authProviders.value = await $fetch<AuthProvider[]>('/api/v1/auth-providers/')
    }
    catch (error) {
      console.error('Failed to fetch auth providers:', error)
      authProviders.value = []
    }
    finally {
      isLoading.value = false
    }
  }

  return {
    authProviders,
    isLoading,
    fetchAuthProviders,
  }
}
