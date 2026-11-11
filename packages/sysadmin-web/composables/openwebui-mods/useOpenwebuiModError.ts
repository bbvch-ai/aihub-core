export function useOpenwebuiModError() {
  return (error: unknown, fallback: string): string => {
    if (!(error instanceof Error)) return fallback
    const data = 'data' in error ? error.data : null
    const detail = data && typeof data === 'object' && 'detail' in data ? data.detail : null
    if (typeof detail === 'string') return detail
    return error.name === 'FetchError' ? fallback : error.message
  }
}
