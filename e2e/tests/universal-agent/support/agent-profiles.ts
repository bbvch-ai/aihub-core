import { expect, request, type APIRequestContext } from '@playwright/test'

import {
  AGENT_MODEL_PREFIX,
  API_TOKEN,
  API_URL,
  MAIN_LLM,
  TASK_LLM,
  TEMPLATE_PROFILE,
  TENANT,
  UNIVERSAL_AGENT_CLASS,
} from './env'
import type { OpenWebuiApi } from './openwebui-api'

type Configuration = Record<string, unknown>

/** The template's own restrictions would leak into every spec, so a profile starts from none of them. */
const UNRESTRICTED_TOOL_LOOP: ToolLoopOverrides = { disable_tools: false, disabled_tools: [], approvals: [] }

interface AgentInstance {
  agent_id: string
  configuration: Configuration
}

export interface ToolLoopOverrides {
  max_tool_calls?: number
  disable_tools?: boolean
  disabled_tools?: string[]
  approvals?: { tool: string; policy: 'never' | 'every_call' | 'once_per_run' | 'once_per_thread' }[]
}

/** A Universal Agent profile created for one spec file and deleted after it, as OpenWebUI shows it. */
export interface ThrowawayProfile {
  agentId: string
  modelId: string
}

/**
 * Creates and deletes Universal Agent profiles through the AI-Hub API with a superuser token. A profile copies an
 * existing one so it runs on whatever this stack has configured, with the models pinned and user memory off: a fact
 * remembered from an earlier run would let the agent answer without the tool call a spec asserts.
 */
export class AgentProfiles {
  private constructor(private readonly http: APIRequestContext) {}

  static async connect(): Promise<AgentProfiles> {
    const http = await request.newContext({
      ignoreHTTPSErrors: true,
      extraHTTPHeaders: { Authorization: `Bearer ${API_TOKEN}` },
    })
    return new AgentProfiles(http)
  }

  async create(label: string, toolLoop: ToolLoopOverrides): Promise<ThrowawayProfile> {
    const agentId = `e2e-ua-${label}-${Date.now().toString(36)}${Math.random().toString(36).slice(2, 6)}`
    const response = await this.http.post(this.instancesUrl(), {
      data: { agent_id: agentId, configuration: AgentProfiles.configuration(await this.template(), agentId, toolLoop) },
    })
    expect(
      response.status(),
      response.status() === 503
        ? `The ${UNIVERSAL_AGENT_CLASS} class is offline (POST returned 503): start the agent service first.`
        : `Creating profile ${agentId}: ${await response.text()}`,
    ).toBe(201)
    return { agentId, modelId: `${AGENT_MODEL_PREFIX}${UNIVERSAL_AGENT_CLASS}.${agentId}` }
  }

  async delete(profile: ThrowawayProfile): Promise<void> {
    const response = await this.http.delete(`${this.instancesUrl()}/${profile.agentId}`)
    expect([204, 404], `Deleting profile ${profile.agentId}`).toContain(response.status())
  }

  async dispose(): Promise<void> {
    await this.http.dispose()
  }

  /** OpenWebUI lists a new profile only once the API's provisioner has synced it. */
  static async waitUntilListed(owui: OpenWebuiApi, profile: ThrowawayProfile): Promise<void> {
    await expect
      .poll(async () => (await owui.models(true)).some((model) => model.id === profile.modelId), {
        timeout: 60_000,
        intervals: [3_000],
        message: `OpenWebUI lists ${profile.modelId} (provisioner sync, and the e2e user's access to the profile)`,
      })
      .toBe(true)
  }

  private instancesUrl(): string {
    return `${API_URL}/${TENANT}/agents/classes/${UNIVERSAL_AGENT_CLASS}/instances`
  }

  private async template(): Promise<Configuration> {
    const response = await this.http.get(this.instancesUrl())
    await expect(response, `GET ${this.instancesUrl()}`).toBeOK()
    const instances = (await response.json()) as AgentInstance[]
    const template = instances.find((instance) => instance.agent_id === TEMPLATE_PROFILE) ?? instances[0]
    expect(template, `an existing ${UNIVERSAL_AGENT_CLASS} profile to copy`).toBeDefined()
    return template.configuration
  }

  private static configuration(template: Configuration, agentId: string, toolLoop: ToolLoopOverrides): Configuration {
    const name = `E2E ${agentId}`
    const localized = { en: name, de: name, fr: name, it: name }
    const llm = template.llm as Configuration
    return {
      ...template,
      agent_id: agentId,
      name: localized,
      description: localized,
      llm: { ...llm, model_name: MAIN_LLM },
      task_llm: { ...((template.task_llm as Configuration | null) ?? llm), model_name: TASK_LLM },
      user_memory: {
        ...(template.user_memory as Configuration),
        enable_user_memory_retrieval: false,
        enable_user_memory_storage: false,
      },
      knowledge_tool: { ...(template.knowledge_tool as Configuration), every_readable_collection: true },
      tool_loop: { ...(template.tool_loop as Configuration), ...UNRESTRICTED_TOOL_LOOP, ...toolLoop },
    }
  }
}
