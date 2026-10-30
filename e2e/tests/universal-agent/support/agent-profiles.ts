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

/** An agent profile created for one spec file and deleted after it, as OpenWebUI shows it. */
export interface ThrowawayProfile {
  agentId: string
  modelId: string
  agentClass: string
}

/** What a describe block needs besides the defaults: another blueprint, or settings on top of the copied profile. */
export interface ProfileOptions {
  agentClass?: string
  configuration?: Configuration
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

  async create(label: string, toolLoop: ToolLoopOverrides, options: ProfileOptions = {}): Promise<ThrowawayProfile> {
    const agentClass = options.agentClass ?? UNIVERSAL_AGENT_CLASS
    const agentId = `e2e-ua-${label}-${Date.now().toString(36)}${Math.random().toString(36).slice(2, 6)}`
    const configuration = {
      ...AgentProfiles.configuration(await this.template(agentClass), agentId, toolLoop),
      ...options.configuration,
    }
    const response = await this.http.post(this.instancesUrl(agentClass), {
      data: { agent_id: agentId, configuration },
    })
    expect(
      response.status(),
      response.status() === 503
        ? `The ${agentClass} class is offline (POST returned 503): start the agent service first.`
        : `Creating profile ${agentId}: ${await response.text()}`,
    ).toBe(201)
    return { agentId, modelId: `${AGENT_MODEL_PREFIX}${agentClass}.${agentId}`, agentClass }
  }

  async delete(profile: ThrowawayProfile): Promise<void> {
    const response = await this.http.delete(`${this.instancesUrl(profile.agentClass)}/${profile.agentId}`)
    expect([204, 404], `Deleting profile ${profile.agentId}`).toContain(response.status())
  }

  async dispose(): Promise<void> {
    await this.http.dispose()
  }

  /** The pipe can list a profile before its workspace capabilities are provisioned. */
  static async waitUntilListed(owui: OpenWebuiApi, profile: ThrowawayProfile): Promise<void> {
    await expect
      .poll(
        async () =>
          (await owui.models(true)).some(
            (model) => model.id === profile.modelId && model.info?.meta?.capabilities?.terminal === false,
          ),
        {
          timeout: 60_000,
          intervals: [3_000],
          message: `OpenWebUI lists ${profile.modelId} with provisioned capabilities and access`,
        },
      )
      .toBe(true)
  }

  private instancesUrl(agentClass: string): string {
    return `${API_URL}/${TENANT}/agents/classes/${agentClass}/instances`
  }

  /** An existing profile of the class, or else the class's first shipped template, so a fresh stack works too. */
  private async template(agentClass: string): Promise<Configuration> {
    const response = await this.http.get(this.instancesUrl(agentClass))
    await expect(response, `GET ${this.instancesUrl(agentClass)}`).toBeOK()
    const instances = (await response.json()) as AgentInstance[]
    const instance = instances.find((candidate) => candidate.agent_id === TEMPLATE_PROFILE) ?? instances[0]
    if (instance) {
      return instance.configuration
    }
    const detail = await this.http.get(`${API_URL}/${TENANT}/agents/classes/${agentClass}`)
    await expect(detail, `GET the ${agentClass} class`).toBeOK()
    const templates = ((await detail.json()) as { templates: Configuration[] }).templates
    expect(templates[0], `an existing ${agentClass} profile or template to copy`).toBeDefined()
    return templates[0]
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
      ...(template.user_memory
        ? {
            user_memory: {
              ...(template.user_memory as Configuration),
              enable_user_memory_retrieval: false,
              enable_user_memory_storage: false,
            },
          }
        : {}),
      knowledge_tool: { ...(template.knowledge_tool as Configuration), every_readable_collection: true },
      tool_loop: { ...(template.tool_loop as Configuration), ...UNRESTRICTED_TOOL_LOOP, ...toolLoop },
    }
  }
}
