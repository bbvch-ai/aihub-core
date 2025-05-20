import type { TimeRange } from '@core/sdk/client'
import type { GridStackWidget } from 'gridstack/dist/types'

export interface DashboardWidget extends GridStackWidget {
  id: string
  component: string
  timeRange: TimeRange
  agent?: {
    agentId: string
    agentClass: string
  }
  event: string
}
