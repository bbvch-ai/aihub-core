/**
 * Wraps ``useLocalePath()`` to auto-inject the current tenant from the route.
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
  const { tenantName } = useTenant()

  return (path: string) => {
    const tenant = tenantName.value
    if (!tenant) return localePath(path)
    return localePath(`/${tenant}${path}`)
  }
}
