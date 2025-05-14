import {
  DashboardComponentNumber,
  DashboardComponentLineChart,
  DashboardComponentBarChart,
} from '#components'

export const useDashboardComponent = () => {
  const mapping = {
    DashboardComponentNumber,
    DashboardComponentLineChart,
    DashboardComponentBarChart,
  }

  const resolveComponent = (name: string) => {
    if (name in mapping) {
      return mapping[name]
    }
    throw Error(`Unable to resolve component for ${name}`)
  }

  const componentNames = Object.keys(mapping)

  return {
    resolveComponent,
    componentNames,
  }
}
