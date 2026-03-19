<template>
  <ProgressBar
    v-if="threadIsLoading || threadEventsAreLoading || !thread || !threadEvents"
    mode="indeterminate"
    style="height: 2px"
  />
  <div
    v-else
    ref="threadPanelRef"
    class="relative h-[calc(100vh-50px)] w-1/2 min-w-[800px] overflow-y-auto border-l border-surface-200 p-3 dark:border-surface-700"
  >
    <ThreadDetails
      :key="key"
      :events="threadEvents"
      :thread="thread"
      :display-id="route.params.display_id"
    />
    <div
      class="fixed top-1/2 -translate-y-1/2"
      :style="{ left: `${panelLeftPosition - 16}px` }"
    >
      <i
        class="pi pi-chevron-right cursor-pointer rounded-full border border-surface-200 bg-surface-0 p-3 hover:bg-surface-100 dark:border-surface-700 dark:bg-surface-900 hover:dark:bg-surface-800"
        @click="closeThread"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
const route = useRoute()
const router = useRouter()
const localeRoute = useLocaleRoute()

const { thread, threadIsLoading } = useThread()
const { threadEvents, threadEventsAreLoading } = useThreadEvents()

const threadPanelRef = ref(null)
const panelBounding = useElementBounding(threadPanelRef)
const panelLeftPosition = computed(() => panelBounding.left.value)

const key = computed(() => {
  return route.params.thread_id + route.params.display_id
})

const closeThread = () => {
  router.push(localeRoute('/service/openai'))
}
</script>
