import { listUserFiles } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'

export const useUserFiles = defineQuery(() => {
  const { tenantId } = useTenant()
  const folder = ref('.')

  const filesQuery = useQuery({
    key: () => ['tenant', tenantId.value, 'user-files', folder.value],
    staleTime: minutesToMilliseconds(5),
    enabled: useTenantReady(),
    query: async () =>
      await listUserFiles({
        composable: '$fetch',
        path: { tenant_id: tenantId.value! },
        query: { folder: folder.value },
      }),
  })

  const entries = computed(() => filesQuery.state.value?.data?.entries ?? [])
  const folderTitle = computed(() => filesQuery.state.value?.data?.folder_title ?? null)
  const isLoading = computed(() => filesQuery.asyncStatus.value === 'loading')

  return { folder, entries, folderTitle, isLoading, error: filesQuery.error, refresh: filesQuery.refetch }
})
