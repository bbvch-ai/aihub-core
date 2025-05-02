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
    <h1 class="text-3xl font-bold">
      Thread: {{ thread.name }}
    </h1>
    <Panel
      class="panel pt-5"
    >
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <span class="font-semibold">
            First Interaction:
          </span>
          <Tag
            :value="formattedDate(thread.first_interaction)"
            severity="secondary"
          />
        </div>
        <div class="flex items-center gap-2">
          <span class="font-semibold">
            Last Interaction:
          </span>
          <Tag
            :value="formattedDate(thread.latest_interaction)"
            severity="secondary"
          />
        </div>
        <div class="flex items-center gap-2">
          <span class="font-semibold">
            Pending:
          </span>
          <Tag
            v-if="thread.has_pending"
            severity="warn"
            :value="pendingType(thread)"
          />
          <Tag
            v-else
            severity="success"
            value="No"
          />
        </div>
        <div class="flex items-center gap-2">
          <span class="font-semibold">
            Status:
          </span>
          <Tag
            v-if="thread.has_errors"
            severity="danger"
            value="Error"
          />
          <Tag
            v-else
            severity="success"
            value="Successfull"
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
