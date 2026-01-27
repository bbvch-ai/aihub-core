<template>
  <StructuralColumn
    :title="t('thread.events.title')"
    :close-route="`/service/threads/${route.params.thread_id}/display`"
    :loading="threadIsLoading || threadEventsAreLoading"
  >
    <EventList
      :thread="thread"
      :events="threadEvents"
      :display-id="route.params.display_id"
    />
  </StructuralColumn>
</template>

<script setup lang="ts">
const { thread, threadIsLoading } = useThread()
const { threadEvents, threadEventsAreLoading } = useThreadEvents()

const route = useRoute()
const { t } = useI18n()
</script>
