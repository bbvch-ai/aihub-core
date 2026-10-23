import { AgentProfiles, type ProfileOptions, type ThrowawayProfile, type ToolLoopOverrides } from './agent-profiles'
import { API_TOKEN, LLM_TEST_TIMEOUT } from './env'
import { expect, test } from './openwebui-test'
import { Preflight } from './preflight'

/**
 * Gives an `@llm` describe block its own agent profile (a Universal Agent one unless `options` names another class): created and checked before its first test, deleted
 * after its last. The tests of the block run in order in one worker, so they share the profile.
 */
export class ThrowawayProfileFixture {
  static register(
    label: string,
    toolLoop: ToolLoopOverrides = {},
    options: ProfileOptions = {},
  ): () => ThrowawayProfile {
    let profiles: AgentProfiles | undefined
    let profile: ThrowawayProfile | undefined

    test.describe.configure({ mode: 'default', retries: 1, timeout: LLM_TEST_TIMEOUT })
    test.skip(!API_TOKEN, 'E2E_API_TOKEN is not set: the @llm specs create throwaway profiles with a superuser token.')

    test.beforeAll(async ({ owui }) => {
      profiles = await AgentProfiles.connect()
      profile = await profiles.create(label, toolLoop, options)
      await AgentProfiles.waitUntilListed(owui, profile)
      await Preflight.check(owui, profile.modelId)
    })

    test.afterAll(async () => {
      if (profiles && profile) {
        await profiles.delete(profile)
      }
      await profiles?.dispose()
    })

    return () => {
      expect(profile, 'the throwaway profile was created in beforeAll').toBeDefined()
      return profile as ThrowawayProfile
    }
  }
}
