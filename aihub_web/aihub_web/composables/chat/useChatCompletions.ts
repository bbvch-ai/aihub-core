import {
  type ChatCompletionAssistantMessageParam,
  type ChatCompletionDeveloperMessageParam, type ChatCompletionFunctionMessageParam,
  type ChatCompletionSystemMessageParam, type ChatCompletionToolMessageParam, type ChatCompletionUserMessageParam,
  chatCompletionWithAssistants,
} from '@core/sdk/client'

type MessageType = Array<ChatCompletionDeveloperMessageParam | ChatCompletionSystemMessageParam | ChatCompletionUserMessageParam | ChatCompletionAssistantMessageParam | ChatCompletionToolMessageParam | ChatCompletionFunctionMessageParam>

export const useChatCompletions = defineMutation(() => {
  const { mutate: sendMessages } = useMutation({
    mutation: ({ model, messages, threadId }: { model: string, messages: MessageType, threadId: string }) =>
      chatCompletionWithAssistants({
        composable: '$fetch',
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
