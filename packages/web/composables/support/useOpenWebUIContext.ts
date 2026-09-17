export interface OpenWebUIContext {
  threadId: string
  displayId: string
  model?: string
}

// The chat UI runs inside an iframe (pages/[tenant]/service/openai.vue), so the
// shell never sees which conversation the user is looking at — the pipe tells it,
// by posting `set-context` as each message streams. Keeping the last one is what
// lets a bug report name the exact thread, which is the only handle that survives
// the user's own retelling: support can replay the run's events and trace from it.
export const useOpenWebUIContext = () => {
  const context = useState<OpenWebUIContext | null>('openwebui-context', () => null)

  const setOpenWebUIContext = (next: OpenWebUIContext): void => {
    context.value = next
  }

  const clearOpenWebUIContext = (): void => {
    context.value = null
  }

  return { context, setOpenWebUIContext, clearOpenWebUIContext }
}
