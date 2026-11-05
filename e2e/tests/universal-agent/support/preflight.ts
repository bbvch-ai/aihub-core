import { expect } from '@playwright/test'

import type { OpenWebuiApi } from './openwebui-api'

const USER_FILES_FILTER = 'aihub-feature-user-files'

/**
 * Stack problems that would otherwise surface minutes later as a confusing LLM-test failure. The Universal Agent
 * class being offline is caught where a profile is created (503). Whether the e2e user's OpenWebUI account is
 * linked to an AI-Hub user cannot be told from the browser, so it is not checked here; see README.md.
 */
export class Preflight {
  static async check(owui: OpenWebuiApi, agentModelId: string): Promise<void> {
    await Preflight.openWebuiFunctionsCurrent(owui, agentModelId)
  }

  /**
   * OpenWebUI functions are deployed separately from the agents; a stack whose functions predate the My Files
   * toggle runs a pipe that does not match the agents. Admins can list the functions; for anyone else the
   * agent model's toggle filters show whether the function exists.
   */
  private static async openWebuiFunctionsCurrent(owui: OpenWebuiApi, agentModelId: string): Promise<void> {
    const stale = `OpenWebUI functions are stale: ${USER_FILES_FILTER} is missing. Redeploy the functions from infra/configs/openwebui/functions.`
    const functionIds = await owui.functionIds()
    if (functionIds !== null) {
      expect(functionIds, stale).toContain(USER_FILES_FILTER)
      return
    }
    const model = (await owui.models()).find((candidate) => candidate.id === agentModelId)
    expect((model?.filters ?? []).map((filter) => filter.id), stale).toContain(USER_FILES_FILTER)
  }
}
