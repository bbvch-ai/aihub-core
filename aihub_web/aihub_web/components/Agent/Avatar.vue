<template>
  <div class="flex gap-2">
    <Avatar
      :size="size"
      icon="pi pi-verified"
    >
      <Icon
        :name="agent.agent_config.icon"
      />
    </Avatar>
    <div
      class="mb-1 flex flex-col justify-center"
    >
      <p
        class="font-bold"
        :class="{ 'text-xs': size === 'normal', 'text-sm': size === 'large' }"
      >
        {{ agent.agent_config.name }}
      </p>
      <p
        :class="{ 'text-xs': size === 'normal', 'text-sm': size === 'large' }"
      >
        {{ agent.agent_class }} / {{ agent.agent_id }}
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import Avatar from 'primevue/avatar'

import type { FullAgentInstanceDto, MinimalAgentInstanceDto } from '@core/sdk/client'

withDefaults(defineProps<{
  size?: 'normal' | 'large'
  agent: FullAgentInstanceDto | MinimalAgentInstanceDto
}>(), {
  size: 'large',
})
</script>
