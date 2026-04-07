import {
  initiateDocumentUpload,
  validateDocumentUpload,
  type DocumentUploadRequest,
  type DocumentUploadValidationRequest,
} from '@core/sdk/client'

export interface UploadFileOptions {
  filename: string
  file: File
  namespace: string
  database: string
  tenantId: string
  onProgress?: () => void
}

// Map extensions to MIME types for files where browser fails
const MIME_TYPE_OVERRIDES: Record<string, string> = {
  '.md': 'text/markdown',
  '.markdown': 'text/markdown',
}

const getMimeType = (file: File): string => {
  if (file.type) {
    return file.type
  }

  const ext = '.' + (file.name.split('.').pop()?.toLowerCase() ?? '')
  return MIME_TYPE_OVERRIDES[ext] || 'application/octet-stream'
}

export const useFileUpload = defineMutation(() => {
  const queryCache = useQueryCache()

  const { mutateAsync: uploadFileMutation } = useMutation({
    mutation: async (options: UploadFileOptions) => {
      const { filename, file, namespace, database, tenantId } = options

      const contentType = getMimeType(file)

      const initiateRequest: DocumentUploadRequest = {
        filename,
        content_type: contentType,
        content_length: file.size,
      }

      const initiateResponse = await initiateDocumentUpload({
        composable: '$fetch',
        body: initiateRequest,
        path: {
          tenant_id: tenantId,
          database,
          namespace,
        },
      })

      await fetch(initiateResponse.upload_url, {
        method: 'PUT',
        body: file,
        headers: {
          'Content-Type': contentType,
        },
      })

      const validationRequest: DocumentUploadValidationRequest = {
        file_path: initiateResponse.object_key,
      }

      await validateDocumentUpload({
        composable: '$fetch',
        body: validationRequest,
        path: {
          tenant_id: tenantId,
          database,
          namespace,
        },
      })

      return initiateResponse.upload_id
    },
    onSuccess: (data, variables) => {
      queryCache.invalidateQueries({
        key: ['knowledge', 'databases', variables.database, 'namespaces', variables.namespace, 'documents'],
      })
    },
  })

  return {
    uploadFile: uploadFileMutation,
  }
})
