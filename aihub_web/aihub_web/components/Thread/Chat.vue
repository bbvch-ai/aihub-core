<template>
  <div>
    <div
      v-for="display in hierarchy"
      :key="display.display_id"
      class="mt-4 bg-red-600 p-4"
    >
      <p>Display ID: {{ display.display_id }}</p>
      <div
        v-for="run in display.runs"
        :key="run.run_id"
        class="mt-4 bg-blue-600 p-4"
      >
        <p>Run ID: {{ run.run_id }}</p>
        <div
          v-for="event in run.events"
          :key="event.event_data.event_id"
          class="mt-4 bg-yellow-600 p-4"
        >
          <p><strong>Agent Class: {{ event.agent_class }}</strong></p>
          <p>Event ID: {{ event.event_data.event_id }}</p>
          <p>Created: {{ new Date(event.event_data.created_at) }}</p>
          <pre class="text-xs">{{ JSON.stringify(event, undefined, 2) }}</pre>
        </div>
      </div>
    </div>

    <input
      v-model="message"
      type="text"
      placeholder="Message"
      required
    >
    <Button @click="sendEvent">
      Send
    </Button>
    <Button @click="sendReply">
      HITL
    </Button>
  </div>
</template>

<script lang="ts" setup>
import { useThreadHierarchy } from '@core/composables/useThreadHierarchy'

const props = defineProps<{
  threadId: string
}>()

const { hierarchy, sendUserMessageEvent, sendHumanInTheLoopResponse } = useThreadHierarchy(props.threadId)

const message = ref<string>('')

const sendEvent = () => {
  sendUserMessageEvent(message.value)
}
const sendReply = () => {
  sendHumanInTheLoopResponse(message.value)
}
</script>
