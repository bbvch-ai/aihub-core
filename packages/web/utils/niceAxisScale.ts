const NICE_STEP_FACTORS = [1, 2, 2.5, 5, 10]

export interface AxisScale {
  max: number
  tickAmount: number
}

// ApexCharts' own nice scale keeps the tick count fixed and rounds the step up, which can more than double the axis
// (10516 with five ticks became 0–25000). Rounding the step to the smallest nice one that fits keeps the tallest bar
// near the top. Counts are whole numbers, so the step is too.
export const niceAxisScale = (largestValue: number, headroom: number, maxIntervals = 5): AxisScale => {
  const target = Math.max(1, largestValue * (1 + headroom))
  const roughStep = target / maxIntervals
  const magnitude = 10 ** Math.floor(Math.log10(roughStep))
  const factor = NICE_STEP_FACTORS.find(candidate =>
    Number.isInteger(candidate * magnitude) && candidate * magnitude >= roughStep,
  ) ?? 10
  const step = Math.max(1, factor * magnitude)
  const max = Math.ceil(target / step) * step
  return { max, tickAmount: max / step }
}
