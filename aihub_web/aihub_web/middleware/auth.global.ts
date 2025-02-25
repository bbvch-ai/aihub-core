export default defineNuxtRouteMiddleware(async (to, _) => {
  const { $auth, $i18n } = useNuxtApp()

  const noAuthPaths = [
    `/${$i18n.locale.value}/auth/login`,
    `/${$i18n.locale.value}/auth/callback`,
    `/${$i18n.locale.value}/health`,
  ]

  if (noAuthPaths.includes(to.path)) {
    return
  }

  const user = await $auth.getUser()
  if (user) {
    return
  }
  else {
    return navigateTo(`/${$i18n.locale.value}/auth/login`)
  }
})
