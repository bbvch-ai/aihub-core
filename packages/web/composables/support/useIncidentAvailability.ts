import { getIncidentAvailability } from '@core/sdk/client'
import { hoursToMilliseconds } from 'date-fns'

// Asked once per app load, and answered 200 on every deployment: the form endpoint itself answers
// 404 where reporting is not configured, and the shell's global error handler would toast that at
// a user who has not clicked anything. The button is drawn only where it leads somewhere.
export const useIncidentAvailability = defineQuery(() => {
  const { data } = useQuery({
    key: () => ['incident-availability'],
    staleTime: hoursToMilliseconds(1),
    query: async () => await getIncidentAvailability({ composable: '$fetch' }),
  })

  const incidentReportingIsAvailable = computed(() => data.value?.enabled === true)

  return { incidentReportingIsAvailable }
})
