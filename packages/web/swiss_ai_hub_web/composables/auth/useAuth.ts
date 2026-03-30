export const useAuth = () => {
  const login = (idpHint?: string) => {
    const { $auth } = useNuxtApp()
    const extraQueryParams = idpHint ? { kc_idp_hint: idpHint } : {}
    $auth.signinRedirect({ extraQueryParams })
  }

  const logout = async () => {
    const { $auth } = useNuxtApp()
    const user = await $auth.getUser()
    await $auth.signoutRedirect({ id_token_hint: user?.id_token })
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
