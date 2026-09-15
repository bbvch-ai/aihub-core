import { minutesToMilliseconds } from 'date-fns'

import { getDefaultAccessRules } from '~/sdk/client'

export const useDefaultTenantAccessRules = defineQuery(() => {
  const {
    data: defaultAccessRules,
    isPending: defaultAccessRulesAreLoading,
    error: defaultAccessRulesError,
  } = useQuery<string[]>({
    key: () => ['admin-tenants', 'default-access-rules'],
    staleTime: minutesToMilliseconds(5),
    query: async () => await getDefaultAccessRules({ composable: '$fetch' }),
  })
  return { defaultAccessRules, defaultAccessRulesAreLoading, defaultAccessRulesError }
})
