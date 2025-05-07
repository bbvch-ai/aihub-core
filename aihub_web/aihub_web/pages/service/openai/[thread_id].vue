<template>
  <ProgressBar
    v-if="threadIsLoading || threadEventsAreLoading || !thread || !threadEvents"
    mode="indeterminate"
    style="height: 2px"
  />
  <div
    v-else
    class="relative h-[calc(100vh-50px)] w-1/2 min-w-[800px] overflow-y-auto border-l border-surface-200 p-3 dark:border-surface-700"
  >
    <ThreadInfo
      :thread="thread"
    />
    <Divider />
    <EventList
      :events="threadEvents"
      :thread="thread"
    />
    <i
      class="pi pi-chevron-right absolute left-0 top-1/2 cursor-pointer rounded-full p-3 text-xl hover:bg-surface-100 hover:dark:bg-surface-800"
      @click="closeThread"
    />
  </div>
</template>

<script setup lang="ts">
const router = useRouter()
const localeRoute = useLocaleRoute()

const { thread, threadIsLoading } = useThread()
const { threadEvents, threadEventsAreLoading } = useThreadEvents()

const closeThread = () => {
  router.push(localeRoute('/service/openai'))
}
</script>

<style scoped>

</style>
