import { getFileUrl } from '@core/sdk/client'

export const useDocumentUrl = () => {
  const getDocumentSourceUrl = async (source: string): Promise<string> => {
    // Remove s3:// prefix if present
    const cleanSource = source.replace(/^s3:\/\//, '')
    const parts = cleanSource.split('/')
    const [container, ...pathParts] = parts
    const filePath = pathParts.join('/')

    const { url } = await getFileUrl({
      composable: '$fetch',
      path: {
        container,
        file_path: filePath,
      },
    })
    return url
  }

  return {
    getDocumentSourceUrl,
  }
}
