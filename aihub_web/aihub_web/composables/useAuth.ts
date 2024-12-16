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
    return `Bearer ${user.access_token}`
  }

  return {
    login,
    logout,
    getUser,
    getBearer,
  }
}
