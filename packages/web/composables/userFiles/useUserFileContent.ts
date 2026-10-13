import { getUserFileContent } from '@core/sdk/client'

export const useUserFileContent = () => {
  const { tenantId } = useTenant()

  const fetchBlob = async (filePath: string, download = false): Promise<Blob> =>
    await getUserFileContent({
      composable: '$fetch',
      path: { tenant_id: tenantId.value! },
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

  return { fetchBlob, download }
}
