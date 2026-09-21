export interface OpenWebUIContext {
  threadId: string
  displayId: string
  // Split rather than one "model or agent" string: an investigation starts from a different
  // place depending on which it was, and the acceptance criteria ask for all three.
  agentClass?: string
  agentName?: string
  model?: string
}

// The chat UI runs inside an iframe (pages/[tenant]/service/openai.vue), so the shell never
// sees which conversation the user is looking at — the pipe tells it, by posting `set-context`
// as each message streams. Keeping the last one is what lets a bug report name the exact
// thread, the one field in the whole report that survives the reporter's own retelling:
// support can replay that run's events and its trace from it.
export const useOpenWebUIContext = () => {
  const context = useState<OpenWebUIContext | null>('openwebui-context', () => null)

  // Replaces, deliberately: the inlet filter sends every field on every turn, and a field it
  // leaves empty has to clear the previous turn's value rather than survive into a report about
  // this one.
  const setOpenWebUIContext = (next: OpenWebUIContext): void => {
    context.value = next
  }

  // Merges, for the one producer that knows a single field: the agent pipe learns the thread
  // after the filter has already described the turn.
  const updateOpenWebUIContext = (partial: Partial<OpenWebUIContext>): void => {
    context.value = { threadId: '', displayId: '', ...(context.value ?? {}), ...partial }
  }

  const clearOpenWebUIContext = (): void => {
    context.value = null
  }

  return { context, setOpenWebUIContext, updateOpenWebUIContext, clearOpenWebUIContext }
}
