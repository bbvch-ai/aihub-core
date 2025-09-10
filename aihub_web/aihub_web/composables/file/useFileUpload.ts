import {
  initiateFileUpload,
  validateFileUpload,
  type FileUploadRequest,
  type FileUploadValidationRequest,
} from '@core/sdk/client'

export interface UploadFileOptions {
  filename: string
  file: File
  namespace: string
  database: string
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
      const { filename, file, namespace, database } = options

      const contentType = getMimeType(file)

      const initiateRequest: FileUploadRequest = {
        filename,
        content_type: contentType,
        content_length: file.size,
        namespace_name: namespace,
        database_name: database,
      }

      const initiateResponse = await initiateFileUpload({
        composable: '$fetch',
        body: initiateRequest,
      })

      await fetch(initiateResponse.upload_url, {
        method: 'PUT',
        body: file,
        headers: {
          'Content-Type': contentType,
        },
      })

      const validationRequest: FileUploadValidationRequest = {
        container: initiateResponse.container,
        file_path: initiateResponse.object_key,
      }

      await validateFileUpload({
        composable: '$fetch',
        body: validationRequest,
      })

      return initiateResponse.upload_id
    },
    onSuccess: (data, variables) => {
      queryCache.invalidateQueries({
        key: ['knowledge', 'databases', variables.database, 'namespaces', variables.namespace, 'documents']
      })
    },
  })

  return {
    uploadFile: uploadFileMutation,
  }
})
