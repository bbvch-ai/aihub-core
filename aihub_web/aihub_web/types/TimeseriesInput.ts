import type { EventTimeseries } from '@core/sdk/client'

export interface TimeseriesInput {
  name: string
  color?: string
  timeseries: EventTimeseries
}
