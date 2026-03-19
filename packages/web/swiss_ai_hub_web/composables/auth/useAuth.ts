export const useAuth = () => {
  const login = (idpHint?: string) => {
    const { $auth } = useNuxtApp()
    const extraQueryParams = idpHint ? { kc_idp_hint: idpHint } : {}
    $auth.signinRedirect({ extraQueryParams })
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

  const getToken = async () => {
    const user = await getUser()
    if (!user) {
      throw new Error('User not logged in')
    }
    return user.access_token
  }

  const getBearer = async () => {
    const token = await getToken()
    return `Bearer ${token}`
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
    getToken,
    getBearer,
    getHeaders,
  }
}
