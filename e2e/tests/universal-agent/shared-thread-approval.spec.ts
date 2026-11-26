import { expect, request, test, type APIRequestContext } from '@playwright/test'

import { AgentProfiles, type ThrowawayProfile } from './support/agent-profiles'
import { API_TOKEN, API_URL, LLM_TEST_TIMEOUT, SECOND_USER_ID, SECOND_USER_TOKEN, TENANT } from './support/env'

const MARKER = 'shared-thread-ok'
const QUESTION = `Run the shell command \`echo ${MARKER}\` with run_command once, then tell me what it printed.`
const REFUSED_ANSWER_TIMEOUT = 30_000

type Event = Record<string, unknown> & { _event_name?: string }
interface ThreadEvent {
  event_name: string
  event: Event
}

/**
 * Only the user who started a run can answer its tool approval. Another member of the shared thread gets a 403 before
 * the answer is stored, so the owner's question stays open and the owner's own answer still runs the call. API only:
 * OpenWebUI has no shared threads.
 */
test.describe('I1 @llm a tool approval in a shared thread', () => {
  test.describe.configure({ mode: 'default', timeout: LLM_TEST_TIMEOUT })
  test.skip(
    !API_TOKEN || !SECOND_USER_TOKEN || !SECOND_USER_ID,
    'Set E2E_API_TOKEN, E2E_SECOND_USER_TOKEN and E2E_SECOND_USER_ID: the spec needs a second tenant member.',
  )

  let profiles: AgentProfiles
  let profile: ThrowawayProfile
  let owner: APIRequestContext
  let member: APIRequestContext

  test.beforeAll(async () => {
    profiles = await AgentProfiles.connect()
    profile = await profiles.create('shared-approval', { approvals: [{ tool: 'run_command', policy: 'every_call' }] })
    owner = await Api.context(API_TOKEN)
    member = await Api.context(SECOND_USER_TOKEN)
  })

  test.afterAll(async () => {
    await profiles?.delete(profile)
    await profiles?.dispose()
    await owner?.dispose()
    await member?.dispose()
  })

  test('only the user who started the run can answer its approval', async () => {
    const api = new Api(profile)
    const threadId = Api.objectId()

    const question = await api.post(owner, 'UserMessageEvent', threadId, {
      messages: [{ role: 'user', blocks: [{ block_type: 'text', text: QUESTION }] }],
      requested_features: ['code_interpreter'],
    })
    expect(question.name, 'the run asks before run_command').toBe('run_command')
    const ownerId = await api.onlyMember(owner, threadId)

    const added = await owner.post(`${API_URL}/${TENANT}/threads/${threadId}/users`, {
      data: { user_id: SECOND_USER_ID },
    })
    await expect(added, 'the owner shares the thread').toBeOK()

    const refused = await member.post(api.eventUrl('ToolApprovalResponseEvent', threadId, question), {
      data: { response: true, request_event: question },
      timeout: REFUSED_ANSWER_TIMEOUT,
    })
    expect(refused.status(), "another member cannot answer the owner's question").toBe(403)
    expect(await refused.text()).toContain('started this run')

    const stored = await api.eventNames(owner, threadId)
    expect(stored, 'the refused answer is not stored').not.toContain('ToolApprovalResponseEvent')
    expect(stored, 'nothing ran').not.toContain('ToolCallApprovedEvent')

    const answered = await api.answerUntilStopped(owner, threadId, question)
    const approved = answered.filter((event) => event._event_name === 'ToolCallApprovedEvent')
    expect(approved.length, "the owner's answer runs the call").toBeGreaterThan(0)
    expect(approved.every((event) => event.approved_by === ownerId)).toBe(true)
    expect(
      answered.some((event) => event._event_name?.endsWith('StopEvent')),
      'the run finishes',
    ).toBe(true)
    expect(JSON.stringify(answered)).toContain(MARKER)

    const responses = (await api.events(owner, threadId)).filter(
      (event) => event._event_name === 'ToolApprovalResponseEvent',
    )
    expect(responses.length, 'one stored answer per question the owner answered').toBe(approved.length)
    expect(responses.every((event) => event.responded_by === ownerId)).toBe(true)
  })
})

class Api {
  constructor(private readonly profile: ThrowawayProfile) {}

  static async context(token: string): Promise<APIRequestContext> {
    return request.newContext({ ignoreHTTPSErrors: true, extraHTTPHeaders: { Authorization: `Bearer ${token}` } })
  }

  static objectId(): string {
    const seconds = Math.floor(Date.now() / 1000)
      .toString(16)
      .padStart(8, '0')
    return seconds + [...Array(16)].map(() => Math.floor(Math.random() * 16).toString(16)).join('')
  }

  /** An answer names the asked run's display, or the API listens on a new one and never sees the run stop. */
  eventUrl(eventName: string, threadId: string, question?: Event, stream = false): string {
    const base = `${API_URL}/${TENANT}/agents/classes/${this.profile.agentClass}/instances/${this.profile.agentId}`
    const displayId = (question?.topic as { display_id?: string } | undefined)?.display_id
    const display = displayId ? `&display_id=${displayId}` : ''
    return `${base}/${eventName}${stream ? '/stream' : ''}?thread_id=${threadId}${display}`
  }

  async post(http: APIRequestContext, eventName: string, threadId: string, data: object): Promise<Event> {
    const response = await http.post(this.eventUrl(eventName, threadId), { data, timeout: 5 * 60_000 })
    await expect(response, `POST ${eventName}`).toBeOK()
    return (await response.json()) as Event
  }

  async onlyMember(http: APIRequestContext, threadId: string): Promise<string> {
    const response = await http.get(`${API_URL}/${TENANT}/threads/${threadId}`)
    await expect(response).toBeOK()
    const users = ((await response.json()) as { users: { id: string }[] }).users
    expect(users, "the run's user is the thread's only member so far").toHaveLength(1)
    return users[0].id
  }

  async events(http: APIRequestContext, threadId: string): Promise<Event[]> {
    const response = await http.get(`${API_URL}/${TENANT}/events/agents/threads/${threadId}`)
    await expect(response).toBeOK()
    return ((await response.json()) as ThreadEvent[]).map((entry) => ({
      ...entry.event,
      _event_name: entry.event_name,
    }))
  }

  async eventNames(http: APIRequestContext, threadId: string): Promise<string[]> {
    return (await this.events(http, threadId)).map((event) => event._event_name ?? '')
  }

  /** Answers the open question on the stream endpoint, and any further one the run asks, until the run stops. */
  async answerUntilStopped(http: APIRequestContext, threadId: string, question: Event): Promise<Event[]> {
    const seen: Event[] = []
    let open: Event | undefined = question
    for (let round = 0; open && round < 4; round += 1) {
      const response = await http.post(this.eventUrl('ToolApprovalResponseEvent', threadId, open, true), {
        data: { response: true, request_event: open },
        timeout: 5 * 60_000,
      })
      await expect(response, 'the owner answers on the stream endpoint').toBeOK()
      const events = Api.sse(await response.text())
      seen.push(...events)
      open = events.find((event) => event.tool_call_id !== undefined && event.question !== undefined)
    }
    return seen
  }

  private static sse(body: string): Event[] {
    return body
      .split('\n')
      .filter((line) => line.startsWith('data: ') && line !== 'data: [DONE]')
      .map((line) => JSON.parse(line.slice('data: '.length)) as Event)
  }
}
