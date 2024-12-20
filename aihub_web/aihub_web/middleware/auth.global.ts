export default defineNuxtRouteMiddleware(async (to, _) => {
  const { $auth, $i18n } = useNuxtApp()

  const noAuthPaths = [
    `/${$i18n.locale.value}/auth/login`,
    `/${$i18n.locale.value}/auth/callback`,
    `/${$i18n.locale.value}/health`,
  ]

  console.log('Checking auth for', to.path, noAuthPaths)

  if (noAuthPaths.includes(to.path)) {
    return
  }

  const user = await $auth.getUser()
  console.log('user', user)
  if (user) {
    return
  }
  else {
    return navigateTo(`/${$i18n.locale.value}/auth/login`)
  }
})
