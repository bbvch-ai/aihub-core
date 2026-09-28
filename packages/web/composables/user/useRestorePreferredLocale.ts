/**
 * Applies the language persisted against the Keycloak account once per session.
 *
 * The `i18n_redirected` cookie alone cannot carry the choice across a logout: a
 * round trip through Keycloak can land on a different locale prefix, and
 * @nuxtjs/i18n then rewrites the cookie from that prefix. The server-side value
 * is the only copy that survives that, a cleared cookie, or a second device.
 */
export const useRestorePreferredLocale = () => {
  const { locale } = useI18n()
  const { applyLocale } = useApplyLocale()
  const { myUser } = useMyUser()
  const { updateMyLocale } = useUpdateMyLocale()
  // useState, not a plain ref: the layout may remount, and reapplying would
  // fight a language the user switched to in the meantime.
  const alreadyApplied = useState('preferred-locale-applied', () => false)

  watch(myUser, (user) => {
    if (!user || alreadyApplied.value) return
    alreadyApplied.value = true

    const persisted = user.preferred_locale
    if (!persisted) {
      // First login since the feature shipped: adopt whatever the browser chose
      // so the next logout has something to restore.
      updateMyLocale({ locale: locale.value }).catch((error) => {
        console.error('Failed to seed preferred locale', error)
      })
      return
    }

    if (persisted !== locale.value) {
      // The same full switch as the language selector: without it, FormKit and
      // queries already fetched under the old `lang` header stay untranslated.
      applyLocale(persisted)
    }
  }, { immediate: true })
}
