import { expect } from '@playwright/test'

import { AGENT_MODEL_PREFIX, TEMPLATE_PROFILE, UNIVERSAL_AGENT_CLASS } from './env'
import type { OwuiModel } from './openwebui-api'

/** Picks the existing models the `@ui` specs look at, from OpenWebUI's model list. */
export class ModelCatalog {
  static isAgent(model: OwuiModel): boolean {
    return model.id.startsWith(AGENT_MODEL_PREFIX)
  }

  static universalAgent(models: OwuiModel[]): OwuiModel {
    const prefix = `${AGENT_MODEL_PREFIX}${UNIVERSAL_AGENT_CLASS}.`
    const candidates = models.filter((model) => model.id.startsWith(prefix))
    const model = candidates.find((candidate) => candidate.id === `${prefix}${TEMPLATE_PROFILE}`) ?? candidates[0]
    expect(model, `OpenWebUI lists a ${UNIVERSAL_AGENT_CLASS} profile`).toBeDefined()
    return model
  }

  /** The first plain LLM whose terminal capability is not switched off, or undefined when there is none. */
  static terminalCapableLlm(models: OwuiModel[]): OwuiModel | undefined {
    return models.find((model) => !ModelCatalog.isAgent(model) && model.info?.meta?.capabilities?.terminal !== false)
  }
}
