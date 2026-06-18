/**
 * Wraps ``useLocalePath()`` to auto-inject the tenant segment for the
 * ``/[tenant]/...`` route tree.
 *
 * Only the tenant-scoped ``route.params.tenant`` is injected — sysadmin routes
 * carry the tenant as ``route.params.tenant_id`` but their URLs are absolute
 * (e.g. ``/tenants``), so on those routes this falls back to bare ``localePath``.
 * (This differs from ``useTenant().tenantId``, which intentionally resolves both
 * shapes for data fetching.)
 *
 * Usage:
 * ```ts
 * const tenantPath = useTenantPath()
 * router.push(tenantPath('/service/agents'))
 * // → /{locale}/{tenant}/service/agents
 * ```
 */
export function useTenantPath() {
  const localePath = useLocalePath()
  const route = useRoute()

  return (path: string) => {
    const tenant = route.params.tenant as string | undefined
    if (!tenant) return localePath(path)
    return localePath(`/${tenant}${path}`)
  }
}
