import type { FullAgentInstanceDto } from '@core/sdk/client'

const EXPORT_SCHEMA_VERSION = '1.0'

type AgentConfigExport = {
  schemaVersion: string
  agentClass: string
  agentId: string
  configuration: Record<string, unknown>
}

export const useExportAgentInstance = () => {
  const buildExport = (instance: FullAgentInstanceDto): AgentConfigExport => ({
    schemaVersion: EXPORT_SCHEMA_VERSION,
    agentClass: instance.agent_class,
    agentId: instance.agent_id,
    configuration: instance.configuration ?? {},
  })

  const exportAgentInstance = (instance: FullAgentInstanceDto): void => {
    const blob = new Blob([JSON.stringify(buildExport(instance), null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)

    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = `${instance.agent_config.name}_${instance.agent_id}_config.json`
    anchor.click()

    URL.revokeObjectURL(url)
  }

  return { exportAgentInstance }
}
