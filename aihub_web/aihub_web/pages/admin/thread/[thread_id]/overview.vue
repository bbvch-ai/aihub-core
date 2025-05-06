<template>
  <ProgressBar
    v-if="threadIsLoading || !thread"
    mode="indeterminate"
    style="height: 2px"
  />
  <div
    v-else
    class="flex flex-col gap-16 p-3"
  >
    <Panel
      class="panel pt-5"
    >
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <span class="font-semibold">
            {{ $t('eventList.firstInteraction') }}
          </span>
          <Tag
            :value="formattedDate(thread.first_interaction)"
            severity="secondary"
          />
        </div>
        <div class="flex items-center gap-2">
          <span class="font-semibold">
            {{ $t('eventList.lastInteraction') }}
          </span>
          <Tag
            :value="formattedDate(thread.latest_interaction)"
            severity="secondary"
          />
        </div>
        <div class="flex items-center gap-2">
          <span class="font-semibold">
            {{ $t('eventList.latency') }}
          </span>
          <Tag
            :value="thread.latency + 's'"
            severity="secondary"
          />
        </div>
        <div class="flex items-center gap-2">
          <span class="font-semibold">
            {{ $t('eventList.costs') }}
          </span>
          <Tag
            :value="thread.llm_cost.toFixed(6) + 'CHF'"
            severity="secondary"
          />
        </div>
      </div>
    </Panel>
    <ThreadInfo
      :thread="thread"
    />
    <ThreadStatistics :thread="thread" />
  </div>
</template>

<script setup lang="ts">
const { thread, threadIsLoading } = useThread()
const { pendingType } = useThreadUtils()

const formattedDate = (datestr: string) => useDateFormat(new Date(datestr), 'DD.MM.YYYY HH:mm:ss')
</script>

<style scoped>
::v-deep(.panel) {
  .p-panel-header {
    padding: 0 !important;
  }
}
</style>
