export default defineNuxtRouteMiddleware(async (to, _) => {
  const { $auth } = useNuxtApp()

  if (import.meta.client) {
    const user = await $auth.getUser()
    if (!user && to.path !== '/auth/login' && to.path !== '/auth/callback') {
      return navigateTo('/auth/login')
    }
  }
})
