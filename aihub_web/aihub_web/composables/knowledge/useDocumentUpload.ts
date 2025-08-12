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
      const { filename, file, namespace, database, onProgress } = options

      // Step 1: Request presigned URL from backend
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

      // Update progress
      onProgress?.(25)

      // Step 2: Upload file directly to S3/MinIO using presigned URL
      console.log('Uploading to presigned URL:', initiateResponse.upload_url)
      console.log('File details:', { name: filename, type: file.type, size: file.size })

      try {
        const uploadResponse = await fetch(initiateResponse.upload_url, {
          method: 'PUT',
          body: file,
          headers: {
            'Content-Type': file.type,
          },
        })

        console.log('Upload response status:', uploadResponse.status)
        console.log('Upload response headers:', Object.fromEntries(uploadResponse.headers.entries()))

        if (!uploadResponse.ok) {
          const responseText = await uploadResponse.text()
          console.error('S3 upload failed:', {
            status: uploadResponse.status,
            statusText: uploadResponse.statusText,
            responseText,
            url: initiateResponse.upload_url,
          })
          throw new Error(`S3 upload failed: ${uploadResponse.status} ${uploadResponse.statusText} - ${responseText}`)
        }

        console.log('S3 upload successful')
      }
      catch (error) {
        console.error('S3 upload error details:', error)
        if (error.name === 'TypeError' && error.message.includes('fetch')) {
          throw new Error('Network error during S3 upload. Check CORS configuration.')
        }
        throw error
      }

      // Update progress
      onProgress?.(75)

      // Step 3: Notify backend that upload is complete
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

      // Update progress
      onProgress?.(100)

      return completeResponse.document_id
    },
    onSuccess: () => {
      // Invalidate knowledge-related queries to refresh document lists
      queryCache.invalidateQueries({ key: ['knowledge'] })
    },
  })

  /**
   * Validate file before upload
   */
  const validateFile = (file: File): { isValid: boolean, error?: string } => {
    const maxSize = 10 * 1024 * 1024 // 10MB
    const allowedTypes = [
      'application/pdf',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'text/plain',
      'text/markdown',
    ]

    const allowedExtensions = ['.pdf', '.doc', '.docx', '.txt', '.md', '.markdown']

    if (file.size > maxSize) {
      return {
        isValid: false,
        error: `File "${file.name}" is too large. Maximum size is 10MB.`,
      }
    }

    // Check by MIME type or file extension
    const isValidType = allowedTypes.includes(file.type)
    const isValidExtension = allowedExtensions.some(ext =>
      file.name.toLowerCase().endsWith(ext),
    )

    if (!isValidType && !isValidExtension) {
      return {
        isValid: false,
        error: `File "${file.name}" is not a supported format. Supported formats: PDF, DOC, DOCX, TXT, MD`,
      }
    }

    return { isValid: true }
  }

  return {
    uploadDocument: uploadDocumentMutation,
    validateFile,
  }
})
