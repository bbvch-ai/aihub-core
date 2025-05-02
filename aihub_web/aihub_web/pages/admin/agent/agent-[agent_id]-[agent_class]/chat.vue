<template>
  <div class="relative flex flex-col gap-2 p-3">
    <p class="text-xl font-bold">
      Chat
    </p>
    <div>
      <div />
      <div>
        <Textarea
          v-model="userInput"
          class="w-full"
          auto-resize
          rows="5"
          cols="30"
        />
        <Button
          label="Create Thread and Send"
          class="w-full"
          @click="submitMessage"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { CreateThreadRequest } from '@core/sdk/client'

const userInput = ref<string>('')

const route = useRoute()
const router = useRouter()
const localeRoute = useLocaleRoute()

const { user } = useUser()

const { sendMessages } = useChatCompletions()
const { createNewThread } = useThreadUtils()

const submitMessage = async () => {
  const thread = await createNewThread.mutateAsync({
    name: 'Manually created thread',
    user_ids: [user.value.id],
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
  router.push(localeRoute(`/admin/thread/${thread.id}/chat`))
}
</script>

<style scoped>

</style>
