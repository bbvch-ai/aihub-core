<template>
  <div class="flex gap-2">
    <Avatar
      size="large"
      icon="pi pi-verified"
    >
      <Icon
        :name="agent.agent_config.icon"
        size="xl"
      />
    </Avatar>
    <div
      class="mb-1 flex flex-col justify-center"
    >
      <p class="text-sm font-bold">
        {{ agent.agent_config.name }}
      </p>
      <p class="text-sm">
        {{ agent.agent_class }} / {{ agent.agent_id }}
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { AgentDto } from '@core/sdk/client'

defineProps<{
  agent: AgentDto
}>()
</script>

<style scoped>

</style>
