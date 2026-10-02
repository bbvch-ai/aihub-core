import {
  createUserFolder,
  deleteUserFile,
  getUserFileContent,
  moveUserFile,
  uploadUserFile,
} from '@core/sdk/client'

export const useUserFileActions = () => {
  const { tenantId } = useTenant()
  const queryCache = useQueryCache()
  const path = computed(() => ({ tenant_id: tenantId.value! }))

  const invalidate = () => queryCache.invalidateQueries({ key: ['tenant', tenantId.value, 'user-files'] })

  const upload = async (folder: string, files: File[]) => {
    for (const file of files) {
      await uploadUserFile({ composable: '$fetch', path: path.value, query: { folder }, body: { file } })
    }
    await invalidate()
  }

  const createFolder = async (folderPath: string) => {
    await createUserFolder({ composable: '$fetch', path: path.value, body: { path: folderPath } })
    await invalidate()
  }

  const move = async (source: string, destination: string) => {
    await moveUserFile({ composable: '$fetch', path: path.value, body: { source, destination } })
    await invalidate()
  }

  const remove = async (filePath: string) => {
    await deleteUserFile({ composable: '$fetch', path: path.value, query: { path: filePath } })
    await invalidate()
  }

  const fetchBlob = async (filePath: string, download = false): Promise<Blob> =>
    await getUserFileContent({
      composable: '$fetch',
      path: path.value,
      query: { path: filePath, download },
      responseType: 'blob',
    }) as Blob

  const download = async (filePath: string, name: string) => {
    const url = URL.createObjectURL(await fetchBlob(filePath, true))
    const link = document.createElement('a')
    link.href = url
    link.download = name
    link.click()
    URL.revokeObjectURL(url)
  }

  return { upload, createFolder, move, remove, fetchBlob, download }
}
