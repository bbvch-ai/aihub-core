import {
  createThread,
  type CreateThreadRequest,
  type DisplayStatistics,
  type RunStatistics,
  type ThreadDto,
  type WsServerEvent,
} from '@core/sdk/client'

export const useThreadUtils = () => {
  const { t } = useI18n()

  const pendingType = (thread: ThreadDto) => {
    if (thread.open_hitl) {
      return t('threadUtils.pendingTypes.hitl')
    }
    if (thread.open_aitl) {
      return t('threadUtils.pendingTypes.aitl')
    }
    if (thread.open_bitl) {
      return t('threadUtils.pendingTypes.bitl')
    }
    return t('threadUtils.pendingTypes.unknown')
  }

  const runForEvent = (thread: ThreadDto, event: WsServerEvent) => {
    const display = thread?.displays?.find((display: DisplayStatistics) => display.display_id == event.display_id)
    return display?.runs?.find((run: RunStatistics) => run.run_id == event.run_id)
  }

  const createNewThread = useMutation({
    mutation: ({ name, user_ids, agents }: CreateThreadRequest) =>
      createThread({
        composable: '$fetch',
        body: {
          name,
          user_ids,
          agents,
        },
      }),
  })

  return {
    pendingType,
    runForEvent,
    createNewThread,
  }
}
