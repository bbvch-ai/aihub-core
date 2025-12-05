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
const route = useRoute()
const { agent, agentIsLoading } = useAgent()
const { agentConfiguration, agentConfigurationIsLoading } = useAgentConfiguration()
const { updateAgentConfiguration } = useUpdateAgentConfiguration()
const { t } = useI18n()
const toast = useToast()

const configForm = computed(() => agent.value?.agent_config?.form || [])
const configurationData = computed(() => agentConfiguration.value?.configuration || {})

const submitConfiguration = async (formData: Record<string, unknown>) => {
  const agentClass = route.params.agent_class as string
  const agentId = route.params.agent_id as string

  try {
    await updateAgentConfiguration({
      agentClass,
      agentId,
      configuration: formData,
    })
    toast.add({
      severity: 'success',
      summary: t('agent.configuration.saveSuccess'),
      life: 3000,
    })
  }
  catch (error) {
    console.error('Failed to save agent configuration:', error)
    toast.add({
      severity: 'error',
      summary: t('agent.configuration.saveError'),
      life: 5000,
    })
  }
}
</script>
