<template>
  <MemoryManagementPage
    translation-prefix="agent"
    :context-name="agent?.agent_config.name ?? ''"
    :context-loading="agentIsLoading"
    :memory-context="{
      type: 'user',
      agent_class: route.params.agent_class as string,
      agent_id: route.params.agent_id as string,
    }"
    :base-path="`/service/agents/${route.params.agent_class}-${route.params.agent_id}/memories`"
    hide-agent-column
  />
</template>

<script setup lang="ts">
const route = useRoute()

// Get agent info
const { agent, agentIsLoading } = useAgent()
</script>
