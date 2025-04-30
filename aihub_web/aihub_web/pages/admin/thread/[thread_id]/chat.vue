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
import { useUserStore } from '@core/stores/useUserStore'

const route = useRoute()

const { data: thread } = useThread()

const eventStore = useEventsStore()
const userStore = useUserStore()

const { user } = storeToRefs(userStore)

const events = eventStore.eventsForThread(route.params.thread_id)
const userInput = ref('')

const submitMessage = async () => {
  eventStore.sendUserMessageEvent(thread.value.id, userInput.value, user.value)
  userInput.value = ''
}
</script>

<style scoped>

</style>
