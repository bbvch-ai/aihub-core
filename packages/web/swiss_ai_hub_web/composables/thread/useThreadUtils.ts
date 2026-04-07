import {
  createThread,
  type CreateThreadRequest,
  type DisplayStatistics,
  type RunStatistics,
  type ThreadDto,
  type ContextualizedAgentEvent,
} from '@core/sdk/client'

export const useThreadUtils = () => {
  const { t } = useI18n()

  const pendingType = (thread: ThreadDto) => {
    if (thread.open_hitl) {
      return t('thread.utils.pendingTypes.hitl')
    }
    if (thread.open_aitl) {
      return t('thread.utils.pendingTypes.aitl')
    }
    if (thread.open_bitl) {
      return t('thread.utils.pendingTypes.bitl')
    }
    return t('thread.utils.pendingTypes.unknown')
  }

  const runForEvent = (thread: ThreadDto, event: ContextualizedAgentEvent) => {
    const display = thread?.displays?.find((display: DisplayStatistics) => display.display_id == event.display_id)
    return display?.runs?.find((run: RunStatistics) => run.run_id == event.run_id)
  }

  const createNewThread = useMutation({
    mutation: ({ name, user_ids, agents, tenantId }: CreateThreadRequest & { tenantId: string }) =>
      createThread({
        composable: '$fetch',
        path: { tenant_id: tenantId },
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
