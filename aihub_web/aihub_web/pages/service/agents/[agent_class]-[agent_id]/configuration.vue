<template>
  <StructuralColumn
    :title="agent?.agent_config.name"
    close-route="/service/agents"
    :loading="agentIsLoading"
    size="large"
  >
    <div class="flex flex-col gap-12">
      <Panel
        :header="t('agent.configuration.title')"
        toggleable
      >
        <p class="mb-4 text-sm text-surface-500 dark:text-surface-400">
          {{ t('agent.configuration.description') }}
        </p>
        <AgentConfiguration
          v-if="configForm && configForm.length > 0 && !agentConfigurationIsLoading"
          class="w-full"
          :title="t('agent.configuration.runtimeSettings')"
          :description="agent?.agent_config.description || ''"
          :form="configForm"
          :initial-data="configurationData"
          @submit="submitConfiguration"
        />
        <div
          v-else-if="agentConfigurationIsLoading"
          class="text-center text-sm text-surface-500 dark:text-surface-400"
        >
          {{ t('common.loading') }}
        </div>
        <div
          v-else
          class="text-center text-sm text-surface-500 dark:text-surface-400"
        >
          {{ t('agent.configuration.noConfiguration') }}
        </div>
      </Panel>
    </div>
  </StructuralColumn>
</template>

<script setup lang="ts">
const { agent, agentIsLoading } = useAgent()
const { agentConfiguration, agentConfigurationIsLoading } = useAgentConfiguration()
const { t } = useI18n()

const configForm = computed(() => agent.value?.agent_config?.form || [])
const configurationData = computed(() => agentConfiguration.value?.configuration || {})

const submitConfiguration = async (formData: Record<string, unknown>) => {
  // TODO: Implement configuration submission when backend endpoint is ready
  // Expected endpoint: PUT /agents/{agent_class}/{agent_id}/configuration
  console.log('Submitting agent configuration:', formData)
}
</script>
