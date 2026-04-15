<template>
  <MemoryManagementPage
    translation-prefix="agent"
    :context-name="agentInstance?.agent_config.name ?? ''"
    :context-loading="agentInstanceIsLoading"
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

const { agentInstance, agentInstanceIsLoading } = useAgentInstance()
</script>
