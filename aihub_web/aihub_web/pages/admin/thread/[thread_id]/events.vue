<template>
  <div
    v-if="thread && events"
  >
    <EventList
      :events="events"
      :thread="thread"
    />
  </div>
</template>

<script setup lang="ts">
import useThread from '@core/composables/useThread'
import useThreadEvents from '@core/composables/useThreadEvents'

const { data: thread } = useThread()
const { data: events } = useThreadEvents()
</script>

<style scoped>

</style>
