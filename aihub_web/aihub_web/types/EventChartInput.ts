import type { TimeseriesInput } from '@core/types/TimeseriesInput'

export interface EventChartInput {
  title: string
  isLoading: boolean
  timeseriesInputs: TimeseriesInput[]
}
