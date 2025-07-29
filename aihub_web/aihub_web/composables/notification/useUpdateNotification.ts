import { updateNotification, type UpdateNotificationRequest } from '@core/sdk/client'

import type { Ref } from 'vue'

export const useUpdateNotification = defineMutation(() => {
  const queryCache = useQueryCache()
  return useMutation({
    mutation: ({ id, payload }: { id: string, payload: Ref<UpdateNotificationRequest> }) =>
      updateNotification({
        composable: '$fetch',
        path: { notification_id: id },
        body: payload,
      }),
    onSuccess: () => {
      queryCache.invalidateQueries({ key: ['notifications'] })
    },
  })
})
