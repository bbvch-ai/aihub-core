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
import type {
  ChatMessageInput,
  MinimalAgentDto,
  ThreadDto,
  UserDto,
  WsServerEvent,
} from '@core/sdk/client'

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

const user = computed<UserDto>(() => props.thread.users.at(-1)!)

const getAgentDto = (agent_class: string, agent_id: string) =>
  props.thread.participating_agents.find(
    (agent: MinimalAgentDto) =>
      agent.agent_id === agent_id && agent.agent_class === agent_class,
  )

const createUserMessage = (
  blocks: ChatMessageInput['blocks'],
  timestamp: number,
): ExtendedChatMessage => ({
  role: 'user',
  blocks,
  name: user.value.name,
  preferredUsername: user.value.email,
  userImage: user.value.profile_image,
  date: new Date(timestamp / 1_000_000),
})

const createAssistantMessage = (
  text: string,
  event: WsServerEvent,
  timestamp: number,
): ExtendedChatMessage => {
  const agentDto = getAgentDto(event.agent_class, event.agent_id)
  return {
    role: 'assistant',
    blocks: [{ block_type: 'text', text }],
    name: agentDto?.agent_config?.name ?? 'Assistant',
    preferredUsername: `${event.agent_class}/${event.agent_id}`,
    icon: agentDto?.agent_config?.icon,
    date: new Date(timestamp / 1_000_000),
  }
}

const messages = computed<ExtendedChatMessage[]>(() => {
  const msgs: ExtendedChatMessage[] = []

  for (const event of props.events) {
    const { _parent_event_names: types, created_at } = event.event

    if (types.includes('UserMessageEvent')) {
      const blocks = event.event.messages.at(-1)?.blocks ?? []
      msgs.push(createUserMessage(blocks, created_at))
    }

    else if (types.includes('HumanInTheLoopResponseEvent')) {
      msgs.push(createUserMessage(
        [{ block_type: 'text', text: event.event.response }],
        created_at,
      ))
    }

    else if (types.includes('ChunkEvent') && event.event.content) {
      const lastMsg = msgs.at(-1)
      const isSameAgent = lastMsg?.preferredUsername === `${event.agent_class}/${event.agent_id}`

      if (isSameAgent && lastMsg?.role === 'assistant') {
        lastMsg.blocks.push({ block_type: 'text', text: event.event.content })
      }
      else {
        msgs.push(createAssistantMessage(event.event.content, event, created_at))
      }
    }

    else if (types.includes('HumanInTheLoopRequestEvent')) {
      msgs.push(createAssistantMessage(event.event.question, event, created_at))
    }

    else if (types.includes('ExceptionEvent')) {
      msgs.push(createAssistantMessage(event.event.message, event, created_at))
    }
  }

  return msgs
})
</script>

<style scoped>

</style>
