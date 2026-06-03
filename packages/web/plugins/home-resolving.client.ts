// Clears the home-resolving spinner flag once a navigation settles. Lives in a
// plugin, not app.vue: plugins register before the initial navigation, so this
// also catches a full page load that lands on (and redirects off) the home route.
export default defineNuxtPlugin(() => {
  const router = useRouter()
  const homeResolving = useHomeResolving()

  router.afterEach(() => {
    homeResolving.value = false
  })
  router.onError(() => {
    homeResolving.value = false
  })
})
