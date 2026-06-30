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
  onProgress?: (percent: number) => void
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

      await new Promise<void>((resolve, reject) => {
        const xhr = new XMLHttpRequest()

        xhr.open('PUT', initiateResponse.upload_url)
        xhr.setRequestHeader('Content-Type', contentType)
        xhr.upload.onprogress = (e) => {
          if (e.lengthComputable) options.onProgress?.(Math.round((e.loaded / e.total) * 100))
        }
        xhr.onload = () => (xhr.status < 400 ? resolve() : reject(new Error(`Upload failed: ${xhr.status}`)))
        xhr.onerror = () => reject(new Error('Upload network error'))

        xhr.send(file)
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
        key: ['tenant', variables.tenantId, 'knowledge'],
      })
    },
  })

  return {
    uploadFile: uploadFileMutation,
  }
})
