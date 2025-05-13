import {
  DashboardComponentNumber,
  DashboardComponentChart,
} from '#components'

export const useDashboardComponent = () => {
  const mapping = {
    DashboardComponentNumber,
    DashboardComponentChart,
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
