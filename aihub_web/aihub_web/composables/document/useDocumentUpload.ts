import {
  initiateFileUpload,
  type FileUploadRequest,
} from '@core/sdk/client'

export interface UploadFileOptions {
  filename: string
  file: File
  namespace: string
  database: string
  onProgress?: () => void
}

export const useDocumentUpload = defineMutation(() => {
  const queryCache = useQueryCache()

  const { mutateAsync: uploadDocumentMutation } = useMutation({
    mutation: async (options: UploadFileOptions) => {
      const { filename, file, namespace, database } = options

      const initiateRequest: FileUploadRequest = {
        filename,
        content_type: file.type,
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
          'Content-Type': file.type,
        },
      })
      return initiateResponse.upload_id
    },
    onSuccess: () => {
      queryCache.invalidateQueries({ key: ['knowledge'] })
    },
  })

  return {
    uploadDocument: uploadDocumentMutation,
  }
})
