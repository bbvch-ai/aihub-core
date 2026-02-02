<template>
  <div class="flex flex-col gap-8">
    <div
      v-for="(message, index) in messages"
      :key="index"
      class="flex flex-col gap-2"
    >
      <ChatMessage
        is-clickable
        :message="message"
        :name="message.name"
        :email="message.email"
        :date="message.date"
        :image="message.userImage"
        :icon="message.icon"
        @click="() => toDisplay(message)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import type {
  ChatMessageInput,
  MinimalAgentDto,
  ThreadDto,
  MinimalUserDto,
  AgentEventReadable,
} from '@core/sdk/client'

const props = defineProps<{
  events: AgentEventReadable[]
  thread: ThreadDto
}>()

const router = useRouter()
const localeRoute = useLocaleRoute()
const { t } = useI18n()

type ExtendedChatMessage = ChatMessageInput & {
  name: string
  email: string
  date: Date
  userImage?: string
  icon?: string
  displayId: string
}

const user = computed<MinimalUserDto>(() => props.thread.users.at(-1)!)

const getAgentDto = (agent_class: string, agent_id: string) =>
  props.thread.participating_agents.find(
    (agent: MinimalAgentDto) =>
      agent.agent_id === agent_id && agent.agent_class === agent_class,
  )

const toDisplay = (msg: ExtendedChatMessage) => {
  router.push(localeRoute(`/service/threads/${props.thread.id}/display/${msg.displayId}`))
}

const createUserMessage = (
  blocks: ChatMessageInput['blocks'],
  timestamp: number,
  event: AgentEventReadable,
): ExtendedChatMessage => ({
  role: 'user',
  blocks,
  displayId: event.display_id,
  name: user.value.name,
  email: user.value.email,
  userImage: user.value.profile_image,
  date: new Date(timestamp / 1_000_000),
})

const createAssistantMessage = (
  text: string,
  event: AgentEventReadable,
  timestamp: number,
): ExtendedChatMessage => {
  const agentDto = getAgentDto(event.agent_class, event.agent_id)
  return {
    role: 'assistant',
    blocks: [{ block_type: 'text', text }],
    displayId: event.display_id,
    name: agentDto?.agent_config?.name ?? t('chat.assistant'),
    email: `${event.agent_class}/${event.agent_id}`,
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
      msgs.push(createUserMessage(blocks, created_at, event))
    }

    else if (types.includes('HumanInTheLoopResponseEvent')) {
      msgs.push(createUserMessage(
        [{ block_type: 'text', text: event.event.response }],
        created_at,
        event,
      ))
    }

    else if (types.includes('ChunkEvent') && event.event.content) {
      const lastMsg = msgs.at(-1)
      const isSameAgent = lastMsg?.email === `${event.agent_class}/${event.agent_id}`

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
