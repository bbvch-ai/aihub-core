<template>
  <ProgressBar
    v-if="threadIsLoading || !thread"
    mode="indeterminate"
    style="height: 2px"
  />
  <div
    v-else
    ref="memoriesPanelRef"
    class="relative h-[calc(100vh-50px)] w-1/2 min-w-[800px] overflow-y-auto border-l border-surface-200 p-6 dark:border-surface-700"
  >
    <div class="mb-4">
      <h2 class="text-2xl font-semibold">
        {{ t('openwebui.memories.title') }}
      </h2>
    </div>

    <!-- Top-level tabs: One per agent -->
    <TabView v-if="agents.length > 0">
      <TabPanel
        v-for="agent in agents"
        :key="`${agent.agent_class}-${agent.agent_id}`"
        :header="agent.agent_config.name"
      >
        <MemoryOpenWebUIContent
          :agent-class="agent.agent_class"
          :agent-id="agent.agent_id"
        />
      </TabPanel>
    </TabView>

    <!-- Close button -->
    <div
      class="fixed top-1/2 -translate-y-1/2"
      :style="{ left: `${panelLeftPosition - 16}px` }"
    >
      <i
        class="pi pi-chevron-right cursor-pointer rounded-full border border-surface-200 bg-surface-0 p-3 hover:bg-surface-100 dark:border-surface-700 dark:bg-surface-900 hover:dark:bg-surface-800"
        @click="closeMemories"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import type { MinimalAgentDto } from '@core/sdk/client'

const router = useRouter()
const localeRoute = useLocaleRoute()
const { t } = useI18n()

const memoriesPanelRef = ref(null)
const panelBounding = useElementBounding(memoriesPanelRef)
const panelLeftPosition = computed(() => panelBounding.left.value)

// Fetch thread to get agents
const { thread, threadIsLoading } = useThread()

// Get agents from thread
const agents = computed<MinimalAgentDto[]>(() => thread.value?.agents || [])

// Close and return to OpenWebUI
const closeMemories = () => {
  router.push(localeRoute('/service/openai'))
}
</script>
