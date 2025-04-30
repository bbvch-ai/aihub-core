import type { DisplayStatistics, RunStatistics, ThreadDto, WsServerEvent } from '@core/sdk/client'

export default () => {
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

  return {
    pendingType,
    runForEvent,
  }
}
