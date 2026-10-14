import { createIncident, getIncidentForm, type CreatedIncidentDto, type IncidentFormDto } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'

// The form is a file shipped with the platform, so it changes on release, not per request —
// except for the prefilled values, which is why this is still fetched rather than bundled.
export const useIncidentForm = defineQuery(() => {
  const isOpen = useIncidentReport().isOpen

  const {
    data: incidentForm,
    isPending: incidentFormIsLoading,
    error: incidentFormError,
  } = useQuery<IncidentFormDto>({
    key: () => ['incident-form'],
    staleTime: minutesToMilliseconds(5),
    // Only while the dialog is open: a deployment with no incident repository answers 404 here,
    // and there is no reason to ask on every page load for a form nobody has opened.
    enabled: isOpen,
    query: async () => await getIncidentForm({ composable: '$fetch' }),
  })

  return { incidentForm, incidentFormIsLoading, incidentFormError }
})

export const useSubmitIncident = defineMutation(() => {
  const { mutateAsync: submitIncident, isLoading: incidentIsSubmitting } = useMutation({
    mutation: async ({
      submission,
      attachments,
    }: {
      submission: Record<string, unknown>
      attachments: File[]
    }): Promise<CreatedIncidentDto> => {
      // Multipart, so the answers travel as one JSON field beside the files. The API validates
      // that JSON against the form's own schema; sending the fields individually would make the
      // endpoint's shape depend on the form definition.
      return await createIncident({
        composable: '$fetch',
        body: { submission: JSON.stringify(submission), attachments },
      })
    },
  })

  return { submitIncident, incidentIsSubmitting }
})
