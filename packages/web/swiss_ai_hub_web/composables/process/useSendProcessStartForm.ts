import { sendProcessStartForm } from '@core/sdk/client'

export const useSendProcessStartForm = defineMutation(() => {
  const queryCache = useQueryCache()

  const { mutateAsync: sendProcessStartFormMutation } = useMutation({
    mutation: async ({
      processClass,
      processId,
      tenantId,
      submissionRoute,
      submissionMethod,
      data,
    }: {
      processClass: string
      processId: string
      tenantId: string
      submissionRoute: string
      submissionMethod: string
      data: Record<string, unknown>
    }) => {
      console.log('sending', data)
      await sendProcessStartForm({
        composable: '$fetch',
        path: {
          tenant_id: tenantId,
          process_class: processClass,
          process_id: processId,
        },
        query: {
          submission_route: submissionRoute,
          submission_method: submissionMethod,
        },
        body: JSON.parse(JSON.stringify(data)),
      })
      queryCache.invalidateQueries({ key: ['process-instances'] })
      queryCache.invalidateQueries({ key: ['process-walkthroughs'] })
    },
  })
  return {
    sendProcessStartForm: sendProcessStartFormMutation,
  }
})
