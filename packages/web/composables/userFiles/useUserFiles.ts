import { listUserFiles } from '@core/sdk/client'

export const useUserFiles = (folder: Ref<string>) => {
  const { tenantId } = useTenant()

  const filesQuery = useQuery({
    key: () => ['tenant', tenantId.value, 'user-files', folder.value],
    enabled: useTenantReady(),
    query: () =>
      listUserFiles({
        composable: '$fetch',
        path: { tenant_id: tenantId.value! },
        query: { folder: folder.value },
      }),
  })

  const entries = computed(() => filesQuery.state.value?.data?.entries ?? [])
  const folderTitle = computed(() => filesQuery.state.value?.data?.folder_title ?? null)
  const isLoading = computed(() => filesQuery.asyncStatus.value === 'loading')

  return { entries, folderTitle, isLoading, error: filesQuery.error, refresh: filesQuery.refetch }
}
