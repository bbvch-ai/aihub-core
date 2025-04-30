<template>
  <div
    v-if="thread && events"
    class="relative w-full"
  >
    <ChatThread
      :events="events"
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
  </div>
</template>

<script setup lang="ts">
import useThread from '@core/composables/useThread'
import { useEventsStore } from '@core/stores/useEventsStore'

const route = useRoute()

const { data: thread } = useThread()

const eventStore = useEventsStore()

const { mutate: sendMessages } = useChatCompletions()

const events = eventStore.eventsForThread(route.params.thread_id)
const userInput = ref('')

const submitMessage = async () => {
  const agent = thread.value?.agents?.at(0)
  const agentIdentifier = `${agent?.agent_class}/${agent?.agent_id}`
  sendMessages({
    model: agentIdentifier,
    messages: [{ role: 'user', content: userInput.value }],
    threadId: route.params.thread_id,
  })
  userInput.value = ''
}
</script>

<style scoped>

</style>
