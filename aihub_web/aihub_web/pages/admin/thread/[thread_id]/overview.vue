<template>
  <ProgressBar
    v-if="threadIsLoading || !thread"
    mode="indeterminate"
    style="height: 2px"
  />
  <div
    v-else
    class="flex flex-col gap-12 p-3"
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
            {{ $t('eventList.pending') }}
          </span>
          <Tag
            v-if="thread.has_pending"
            severity="warn"
            :value="pendingType(thread)"
          />
          <Tag
            v-else
            severity="success"
            :value="$t('eventList.no')"
          />
        </div>
        <div class="flex items-center gap-2">
          <span class="font-semibold">
            {{ $t('eventList.status') }}
          </span>
          <Tag
            v-if="thread.has_errors"
            severity="danger"
            :value="$t('eventList.error')"
          />
          <Tag
            v-else
            severity="success"
            :value="$t('eventList.successful')"
          />
        </div>
      </div>
    </Panel>
    <ThreadInfo
      :thread="thread"
    />
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
