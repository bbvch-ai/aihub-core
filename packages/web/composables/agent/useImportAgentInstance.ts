export const SUPPORTED_SCHEMA_VERSIONS = ['1.0']

export type AgentConfig = {
  schemaVersion: string
  agentClass: string
  agentId?: string
  configuration: Record<string, unknown>
}

export type AgentConfigImportReason = 'invalidJson' | 'invalidStructure' | 'missingFields' | 'unsupportedVersion'

export class AgentConfigImportError extends Error {
  readonly reason: AgentConfigImportReason

  constructor(reason: AgentConfigImportReason) {
    super(reason)
    this.name = 'AgentConfigImportError'
    this.reason = reason
  }
}

const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === 'object' && value !== null && !Array.isArray(value)

const parseAgentConfigExport = (text: string): AgentConfig => {
  let parsed: unknown
  try {
    parsed = JSON.parse(text)
  }
  catch {
    throw new AgentConfigImportError('invalidJson')
  }

  if (!isRecord(parsed)) throw new AgentConfigImportError('invalidStructure')

  const { schemaVersion, agentClass, agentId, configuration } = parsed

  if (typeof schemaVersion !== 'string' || typeof agentClass !== 'string' || !agentClass || !isRecord(configuration)) {
    throw new AgentConfigImportError('missingFields')
  }

  if (!SUPPORTED_SCHEMA_VERSIONS.includes(schemaVersion)) {
    throw new AgentConfigImportError('unsupportedVersion')
  }

  return {
    schemaVersion,
    agentClass,
    agentId: typeof agentId === 'string' ? agentId : undefined,
    configuration,
  }
}

export const useImportAgentInstance = () => {
  const readAgentConfigFile = async (file: File): Promise<AgentConfig> => {
    const text = await file.text()
    return parseAgentConfigExport(text)
  }

  return { readAgentConfigFile }
}
