import {
  initiateDocumentUpload,
  completeDocumentUpload,
  type DocumentUploadRequest,
  type DocumentUploadCompleteRequest,
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
      const { filename, file, namespace, database} = options

      const initiateRequest: DocumentUploadRequest = {
        filename,
        content_type: file.type,
        content_length: file.size,
        namespace,
        database,
      }

      const initiateResponse = await initiateDocumentUpload({
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

      const completeRequest: DocumentUploadCompleteRequest = {
        upload_id: initiateResponse.upload_id,
        container: initiateResponse.container,
        object_key: initiateResponse.object_key,
        namespace,
        database,
      }

      const completeResponse = await completeDocumentUpload({
        composable: '$fetch',
        body: completeRequest,
      })

      return completeResponse.document_id
    },
    onSuccess: () => {
      queryCache.invalidateQueries({ key: ['knowledge'] })
    },
  })

  return {
    uploadDocument: uploadDocumentMutation,
  }
})
