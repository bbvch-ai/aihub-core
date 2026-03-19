const EVENT_COLOR_PALETTE = [
  '#34d399', '#fbbf24', '#60a5fa', '#c084fc', '#f87171',
  '#fb923c', '#2dd4bf', '#a78bfa', '#f472b6', '#facc15',
  '#4ade80', '#38bdf8', '#e879f9', '#a3e635', '#818cf8',
]

const FALLBACK_COLOR = '#94a3b8'

const hashString = (str: string): number => {
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    hash = ((hash << 5) - hash) + str.charCodeAt(i)
    hash = hash & hash
  }
  return Math.abs(hash)
}

export const useEventColor = () => {
  const getEventColor = (eventName: string): string => {
    if (!eventName) return FALLBACK_COLOR
    return EVENT_COLOR_PALETTE[hashString(eventName) % EVENT_COLOR_PALETTE.length]
  }

  return { getEventColor }
}
