<template>
  <div class="flex flex-col gap-8">
    <div
      v-for="(message, index) in messages"
      :key="index"
      class="flex flex-col gap-2"
    >
      <ChatMessage
        :message="message"
        :name="message.name"
        :preferred-username="message.preferredUsername"
        :date="message.date"
        :image="message.userImage"
        :icon="message.icon"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import type { ChatMessageInput, MinimalAgentDto, ThreadDto, UserDto, WsServerEvent } from '@core/sdk/client'

const props = defineProps<{
  events: WsServerEvent[]
  thread: ThreadDto
}>()

type ExtendedChatMessage = ChatMessageInput & {
  name: string
  preferredUsername: string
  date: Date
  userImage?: string
  icon?: string
}

const user = computed<UserDto>(() => {
  return props.thread.users.at(-1)
})

const getAgentDto = (agent_class: string, agent_id: string) => {
  return props.thread.participating_agents.find((agent: MinimalAgentDto) => {
    return agent.agent_id === agent_id && agent.agent_class === agent_class
  })
}

const messages = computed<ExtendedChatMessage[]>(() => {
  const msgs: ExtendedChatMessage[] = []
  props.events.forEach((event: WsServerEvent) => {
    const agentDto = getAgentDto(event.agent_class, event.agent_id)
    if (event.event._parent_event_names.includes('UserMessageEvent')) {
      msgs.push({
        role: 'user',
        blocks: event.event.messages.at(-1).blocks,
        name: user.value.name,
        preferredUsername: user.value.email,
        userImage: user.value.profile_image,
        date: new Date(event.event.created_at / 1_000_000),
      })
    }
    if (event.event._parent_event_names.includes('HumanInTheLoopResponseEvent')) {
      msgs.push({
        role: 'user',
        blocks: [{ block_type: 'text', text: event.event.response }],
        name: user.value.name,
        preferredUsername: user.value.email,
        userImage: user.value.profile_image,
        date: new Date(event.event.created_at / 1_000_000),
      })
    }
    if (event.event._parent_event_names.includes('ChunkEvent') && event.event.content) {
      if (msgs.at(-1)?.preferredUsername === `${event.agent_class}/${event.agent_id}`) {
        const lastMessage = msgs.at(-1)
        lastMessage.blocks.push({ block_type: 'text', text: event.event.content })
      }
      else {
        msgs.push({
          role: 'assistant',
          blocks: [{ block_type: 'text', text: event.event.content }],
          name: agentDto?.agent_config?.name,
          preferredUsername: `${event.agent_class}/${event.agent_id}`,
          date: new Date(event.event.created_at / 1_000_000),
          icon: agentDto?.agent_config?.icon,
        })
      }
    }
    if (event.event._parent_event_names.includes('HumanInTheLoopRequestEvent')) {
      msgs.push({
        role: 'assistant',
        blocks: [{ block_type: 'text', text: event.event.question }],
        name: agentDto?.agent_config?.name,
        preferredUsername: `${event.agent_class}/${event.agent_id}`,
        date: new Date(event.event.created_at / 1_000_000),
        icon: agentDto?.agent_config?.icon,
      })
    }
  })
  return msgs
})
</script>

<style scoped>

</style>
