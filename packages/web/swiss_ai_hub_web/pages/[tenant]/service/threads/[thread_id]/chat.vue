<template>
  <StructuralColumn
    :title="t('thread.chat.title')"
    close-route="/service/threads"
    :loading="threadIsLoading || threadEventsAreLoading"
  >
    <ChatThread
      :events="threadEvents"
      :thread="thread"
    />
    <div class="pt-16">
      <Textarea
        v-model="userInput"
        class="w-full"
        auto-resize
        rows="5"
        cols="30"
      />
      <Button
        label="Send new Message"
        class="w-full"
        @click="submitMessage"
      />
    </div>
  </StructuralColumn>
</template>

<script setup lang="ts">
const route = useRoute()

const { thread, threadIsLoading } = useThread()
const { threadEvents, threadEventsAreLoading } = useThreadEvents()
const { t } = useI18n()

const { sendMessages } = useChatCompletions()

const userInput = ref('')

const submitMessage = async () => {
  const agent = thread.value?.agents?.at(0)
  const agentIdentifier = `${agent?.agent_class}/${agent?.agent_id}`
  sendMessages({
    model: agentIdentifier,
    messages: [{ role: 'user', content: userInput.value }],
    threadId: route.params.thread_id as string,
  })
  userInput.value = ''
}
</script>
