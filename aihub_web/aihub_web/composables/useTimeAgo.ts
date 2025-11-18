type TimeAgo = {
  text: string
  severity: 'success' | 'info' | 'warning' | 'danger'
}

export function useTimeAgo() {
  const { t } = useI18n()

  const getTimeAgo = (dateValue: string | number | Date): TimeAgo => {
    const date = new Date(dateValue)
    const now = new Date()
    const diffInSeconds = (now.getTime() - date.getTime()) / 1000

    const minute = 60
    const hour = minute * 60
    const day = hour * 24
    const week = day * 7
    const month = day * 30.44 // Average month length
    const year = day * 365.25 // Account for leap years

    if (diffInSeconds < hour) {
      return { text: t('time_ago.last_hour'), severity: 'success' }
    }
    if (diffInSeconds < day) {
      return { text: t('time_ago.last_day'), severity: 'success' }
    }
    if (diffInSeconds < week) {
      return { text: t('time_ago.last_week'), severity: 'info' }
    }
    if (diffInSeconds < month) {
      return { text: t('time_ago.last_month'), severity: 'warning' }
    }
    if (diffInSeconds < year) {
      return { text: t('time_ago.last_year'), severity: 'danger' }
    }
    return { text: t('time_ago.long_time_ago'), severity: 'danger' }
  }

  return { getTimeAgo }
}
