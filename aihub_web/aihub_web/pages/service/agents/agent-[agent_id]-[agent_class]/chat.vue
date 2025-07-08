<template>
  <StructuralColumn
    :title="t('agent.chat.title')"
    close-route="/service/agents"
  >
    <div class="relative flex flex-col gap-2 p-3">
      <div>
        <div />
        <div>
          <Textarea
            v-model="userInput"
            class="w-full"
            auto-resize
            rows="5"
            cols="30"
            :placeholder="t('agent.chat.placeholder')"
            @keydown.enter="submitMessage"
          />
          <Button
            :label="t('agent.chat.createThreadAndSend')"
            class="w-full"
            :disabled="!userInput"
            @click="submitMessage"
          />
        </div>
      </div>
    </div>
  </StructuralColumn>
</template>

<script setup lang="ts">
import type { CreateThreadRequest } from '@core/sdk/client'

const userInput = ref<string>('')

const route = useRoute()
const router = useRouter()
const localeRoute = useLocaleRoute()
const { t } = useI18n()

const { myUser } = useMyUser()

const { sendMessages } = useChatCompletions()
const { createNewThread } = useThreadUtils()

const submitMessage = async () => {
  const thread = await createNewThread.mutateAsync({
    name: t('agent.chat.manuallyCreatedThread'),
    user_ids: [myUser.value.id],
    agents: [{
      agent_id: route.params.agent_id as string,
      agent_class: route.params.agent_class as string,
    }],
  } satisfies CreateThreadRequest)
  const agentIdentifier = `${route.params.agent_class}/${route.params.agent_id}`
  sendMessages({
    model: agentIdentifier,
    messages: [{ role: 'user', content: userInput.value }],
    threadId: thread.id,
  })
  userInput.value = ''
  router.push(localeRoute(`/service/threads/${thread.id}/chat`))
}
</script>
