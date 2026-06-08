// In a plugin, not app.vue, so afterEach registers before the initial navigation
// — otherwise a full load landing on the home route never clears the flag.
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
