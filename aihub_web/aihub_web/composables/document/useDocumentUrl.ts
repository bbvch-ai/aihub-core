import { getFileUrl } from '@core/sdk/client'

export const useDocumentUrl = () => {
  const getDocumentSourceUrl = async (sourcePath: string): Promise<string> => {
    const parts = sourcePath.split('/')
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
