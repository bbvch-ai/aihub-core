import { uploadUserFile } from '@core/sdk/client'

export const useUploadUserFiles = defineMutation(() => {
  const queryCache = useQueryCache()
  const { tenantId } = useTenant()

  const { mutateAsync: uploadUserFilesMutation, isLoading: isUploading } = useMutation({
    mutation: async ({ folder, files }: { folder: string, files: File[] }) => {
      await Promise.all(
        files.map(file =>
          uploadUserFile({ composable: '$fetch', path: { tenant_id: tenantId.value! }, query: { folder }, body: { file } }),
        ),
      )
    },
    onSettled: () => queryCache.invalidateQueries({ key: ['tenant', tenantId.value, 'user-files'] }),
  })

  return { uploadUserFiles: uploadUserFilesMutation, isUploading }
})
