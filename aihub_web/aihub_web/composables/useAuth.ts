export const useAuth = () => {
  const login = () => {
    const { $auth } = useNuxtApp()
    $auth.signinRedirect()
  }

  const logout = async () => {
    const { $auth } = useNuxtApp()
    await $auth.removeUser()
    navigateTo('/login')
  }

  const getUser = async () => {
    const { $auth } = useNuxtApp()
    return await $auth.getUser()
  }

  const getBearer = async () => {
    const user = await getUser()
    if (!user) {
      throw new Error('User not logged in')
    }
    return `Bearer ${user.access_token}`
  }

  const getHeaders = async (): Promise<Record<string, string>> => {
    const bearer = await getBearer()
    return {
      Authorization: bearer,
    }
  }

  return {
    login,
    logout,
    getUser,
    getBearer,
    getHeaders,
  }
}
