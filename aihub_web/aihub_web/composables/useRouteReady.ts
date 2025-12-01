import { computed } from 'vue'
import { useRoute } from 'vue-router'

/**
 * Check if route parameters are ready for use in API queries.
 * Prevents queries from executing with placeholder values during route transitions.
 *
 * @example
 * const isRouteReady = useRouteReady('dataset_id')
 * const isRouteReady = useRouteReady('agent_id', 'agent_class')
 */
export const useRouteReady = (...paramNames: string[]) => {
  const route = useRoute()

  return computed(() => {
    return paramNames.every((param) => {
      const value = route.params[param]
      return !!value && typeof value === 'string' && !value.startsWith('{')
    })
  })
}
