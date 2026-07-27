import { getDocumentUrl } from '@core/sdk/client'

export const useDocumentUrl = () => {
  const getDocumentSourceUrl = async (tenantId: string, database: string, namespace: string, documentId: string, download = false): Promise<string> => {
    const { url } = await getDocumentUrl({
      composable: '$fetch',
      path: {
        tenant_id: tenantId,
        database,
        namespace,
        document_id: documentId,
      },
      query: { download },
    })
    return url
  }

  return {
    getDocumentSourceUrl,
  }
}
