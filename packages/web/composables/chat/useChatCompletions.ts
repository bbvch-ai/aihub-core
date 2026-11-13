import {
  type ChatCompletionAssistantMessageParam,
  type ChatCompletionDeveloperMessageParam, type ChatCompletionFunctionMessageParam,
  type ChatCompletionSystemMessageParam, type ChatCompletionToolMessageParam, type ChatCompletionUserMessageParam,
  chatCompletionWithAssistants,
} from '@core/sdk/client'

type MessageType = Array<ChatCompletionDeveloperMessageParam | ChatCompletionSystemMessageParam | ChatCompletionUserMessageParam | ChatCompletionAssistantMessageParam | ChatCompletionToolMessageParam | ChatCompletionFunctionMessageParam>

export const useChatCompletions = defineMutation(() => {
  const { getToken } = useAuth()
  const { mutate: sendMessages } = useMutation({
    mutation: async ({ model, messages, threadId, tenantId }: { model: string, messages: MessageType, threadId: string, tenantId: string }) =>
      chatCompletionWithAssistants({
        composable: '$fetch',
        path: { tenant_id: tenantId },
        // Lets an MCP agent profile with auth_mode 'user_token' call its server as this user. Only on the
        // calls that start or continue a run, not on every request.
        headers: { 'X-AIHub-User-Token': await getToken() },
        body: {
          model,
          messages,
          stream: false,
          metadata: {
            thread_id: threadId,
            reconstruct_history: true,
          },
        },
      }),
  })
  return {
    sendMessages,
  }
})
