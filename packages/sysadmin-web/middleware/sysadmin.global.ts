// Global guard for sysadmin-web. Two responsibilities, both intrinsic to being
// a *focused* Nuxt-layer extender of @swiss-ai-hub/web:
//
//  1. Role gate: only AIHubSysAdmin users may use this app. "Am I a sysadmin?"
//     is a user-level question answered authoritatively by the MAIN API
//     (MyTenantController.get_my_tenants); sysadmin-api deliberately doesn't
//     expose it, so we $fetch the main API cross-origin.
//
//  2. Surface confinement: this app extends the web layer and therefore
//     inherits ALL of web's pages (/select-tenant, /[tenant]/service/*, the
//     tenant/OpenWebUI landing flow, …). A focused extender keeps the user
//     inside its OWN section — anything that is not a sysadmin route is sent
//     to the tenant-administration list. (Any customer building a narrow UI
//     on the layer does exactly this; it is the extender's job, not the
//     layer's.)

interface MyTenantsResponse {
  is_sys_admin?: boolean
}

const AUTH_PATH = /^\/(en|de|fr|it)\/auth(\/|$)/
const SYSADMIN_SECTION = /^\/(en|de|fr|it)\/tenants(\/|$)/

export default defineNuxtRouteMiddleware(async (to) => {
  // OIDC callback / silent-renew must complete before we can ask the API
  // anything — never gate or redirect those.
  if (AUTH_PATH.test(to.path)) return

  const { $i18n } = useNuxtApp()
  const locale = $i18n.locale.value
  const config = useRuntimeConfig()
  const mainApiUrl = config.public.mainApi.url
  const { getToken } = useAuth()

  let isSysAdmin = false
  try {
    const token = await getToken()
    const response = await $fetch<MyTenantsResponse>(
      `${mainApiUrl}/api/v1/my-tenants`,
      { headers: token ? { Authorization: `Bearer ${token}` } : {} },
    )
    isSysAdmin = Boolean(response?.is_sys_admin)
  }
  catch (error) {
    console.error('sysadmin middleware: failed to verify sysadmin status', error)
  }

  if (!isSysAdmin) {
    // Not a sysadmin — bounce cross-origin to the main app's tenant selector.
    if (import.meta.client && mainApiUrl) {
      window.location.replace(`${mainApiUrl}/${locale}/select-tenant`)
      return
    }
    return abortNavigation()
  }

  // Sysadmin confirmed. Keep them inside the sysadmin section; everything
  // inherited from the web layer (root landing, /select-tenant,
  // /[tenant]/service/*, …) redirects to the tenant-administration list.
  if (!SYSADMIN_SECTION.test(to.path)) {
    return navigateTo(`/${locale}/tenants`, { replace: true })
  }
})
