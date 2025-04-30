import type { ThreadDto } from '@core/sdk/client'

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
  return {
    pendingType,
  }
}
