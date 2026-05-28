/**
 * Wraps ``useLocalePath()`` to auto-inject the current tenant ID from the route.
 *
 * Usage:
 * ```ts
 * const tenantPath = useTenantPath()
 * router.push(tenantPath('/service/agents'))
 * // → /{locale}/{tenantId}/service/agents
 * ```
 */
export function useTenantPath() {
  const localePath = useLocalePath()
  const { tenantId } = useTenant()

  return (path: string) => {
    const id = tenantId.value
    if (!id) return localePath(path)
    return localePath(`/${id}${path}`)
  }
}
