import { getDocumentUrl } from '@core/sdk/client'

export const useDocumentUrl = () => {
  const getDocumentSourceUrl = async (database: string, namespace: string, documentId: string): Promise<string> => {
    const { url } = await getDocumentUrl({
      composable: '$fetch',
      path: {
        database,
        namespace,
        document_id: documentId,
      },
    })
    return url
  }

  return {
    getDocumentSourceUrl,
  }
}
