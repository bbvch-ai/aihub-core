import { sendProcessStartForm } from '@core/sdk/client'

export const useSendProcessStartForm = defineMutation(() => {
  const queryCache = useQueryCache()

  const { mutateAsync: sendProcessStartFormMutation } = useMutation({
    mutation: async ({
      processClass,
      processId,
      submissionRoute,
      submissionMethod,
      data,
    }: {
      processClass: string
      processId: string
      submissionRoute: string
      submissionMethod: string
      data: Record<string, unknown>
    }) => {
      await sendProcessStartForm({
        composable: '$fetch',
        path: {
          process_class: processClass,
          process_id: processId,
        },
        query: {
          submission_route: submissionRoute,
          submission_method: submissionMethod,
        },
        body: data,
      })
      queryCache.invalidateQueries({ key: ['processes'] })
    },
  })
  return {
    sendProcessStartForm: sendProcessStartFormMutation,
  }
})
