import { changeLocale } from '@formkit/vue'

/**
 * Switches every place the UI language lives, so a restored language and a
 * manual switch cannot drift apart: FormKit's validation messages, the locale
 * route prefix, and query data the API already translated.
 */
export const useApplyLocale = () => {
  const queryCache = useQueryCache()
  const switchLocalePath = useSwitchLocalePath()
  const router = useRouter()

  const applyLocale = async (code: string) => {
    changeLocale(code)
    await router.push(switchLocalePath(code))
    // Query keys carry no locale, so data the API translated under the old
    // `lang` header would otherwise stay cached. Invalidate only after the
    // route change, because the header is read from the live locale.
    queryCache.invalidateQueries()
  }

  return { applyLocale }
}
