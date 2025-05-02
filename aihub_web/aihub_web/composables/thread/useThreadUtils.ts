import {
  createThread,
  type CreateThreadRequest,
  type DisplayStatistics,
  type RunStatistics,
  type ThreadDto,
  type WsServerEvent,
} from '@core/sdk/client'

export const useThreadUtils = () => {
  const pendingType = (thread: ThreadDto) => {
    if (thread.open_hitl) {
      return 'Human in the Loop'
    }
    if (thread.open_aitl) {
      return 'Agent in the Loop'
    }
    if (thread.open_bitl) {
      return 'Bot in the Loop'
    }
    return 'Reason unknown'
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
