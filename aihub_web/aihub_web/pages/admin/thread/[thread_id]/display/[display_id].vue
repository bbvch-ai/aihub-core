<template>
  <StructuralColumn
    :title="t('thread.events.title')"
    :close-route="`/admin/thread/${route.params.thread_id}/display`"
    :loading="threadIsLoading || threadEventsAreLoading"
  >
    <EventList
      :thread="thread"
      :events="threadEvents"
    />
  </StructuralColumn>
</template>

<script setup lang="ts">
const { thread, threadIsLoading } = useThread()
const { threadEvents, threadEventsAreLoading } = useThreadEvents()

const route = useRoute()
const { t } = useI18n()
</script>
