import { getDocumentUrl } from '@core/sdk/client'

export const useDocumentUrl = () => {
  const getDocumentSourceUrl = async (tenantId: string, database: string, namespace: string, documentId: string): Promise<string> => {
    const { url } = await getDocumentUrl({
      composable: '$fetch',
      path: {
        tenant_id: tenantId,
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
