<template>
  <ProgressBar
    v-if="agentIsLoading || !agent"
    mode="indeterminate"
    style="height: 2px"
  />
  <div
    v-else
    class="flex flex-col gap-8 p-3"
  >
    <div>
      <p class="text-xl font-bold">
        {{ agent?.agent_config.name }}
      </p>
      <p class="text-sm">
        {{ agent?.agent_config.description }}
      </p>
    </div>
    <div class="flex flex-col gap-2">
      <p class="text-lg font-bold">
        Start Events
      </p>
      <Panel
        v-for="event in agent?.start_events"
        :key="event.event_name"
        :header="event.event_name"
        toggleable
        collapsed
      >
        <div class="text-sm text-surface-700 dark:text-surface-200">
          {{ event.event_schema.description }}
        </div>
      </Panel>
    </div>
    <div class="flex flex-col gap-2">
      <p class="text-lg font-bold">
        Stop Events
      </p>
      <Panel
        v-for="event in (agent?.stop_events ?? [])"
        :key="event.event_name"
        :header="event.event_name"
        toggleable
        collapsed
      >
        <div class="text-sm text-surface-700 dark:text-surface-200">
          {{ event.event_schema.description }}
        </div>
      </Panel>
    </div>
    <div>
      <p class="text-xl font-bold">
        Config
      </p>
      <div class="rounded-lg border border-surface-300 p-3 dark:border-surface-700">
        <pre class="text-sm">{{ agent?.agent_config }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const { agent, agentIsLoading } = useAgent()
</script>

<style scoped>

</style>
