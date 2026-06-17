<template>
  <StructuralColumn
    :title="t('agent.configuration.title')"
    close-route="/service/agents"
    :loading="agentInstanceIsLoading"
    size="normal"
  >
    <div class="flex flex-col gap-3">
      <p class="mb-4 text-sm text-surface-500 dark:text-surface-400">
        {{ t('agent.configuration.description') }}
      </p>
      <AgentConfiguration
        v-if="configForm && configForm.length > 0 && !agentInstanceIsLoading"
        :title="t('agent.configuration.runtimeSettings')"
        :description="agentInstance?.agent_config.description || ''"
        :form="configForm"
        :initial-data="configurationData"
        @submit="submitConfiguration"
      />
      <div
        v-else-if="agentInstanceIsLoading"
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
    </div>
  </StructuralColumn>
</template>

<script setup lang="ts">
const route = useRoute()
const { tenantId } = useTenant()
const { agentInstance, agentInstanceIsLoading } = useAgentInstance()
const { updateAgentInstance } = useUpdateAgentInstance()
const { t } = useI18n()
const toast = useToast()

const configForm = computed(() => agentInstance.value?.agent_config?.form || [])

// Pass the saved configuration through unchanged. DynamicConfiguration hydrates it
// (seedNullableToggles then seedFormDefaults): non-nullable groups are materialised to
// objects, while nullable groups keep their saved `null` so their "Enable" toggle loads
// off. Pre-filling `null` groups with `{}` here would make every disabled nullable group
// (e.g. reranking_config, org_memory) load as enabled.
const configurationData = computed(
  () => (agentInstance.value?.configuration || {}) as Record<string, unknown>,
)

const submitConfiguration = async (formData: Record<string, unknown>) => {
  const agentClass = route.params.agent_class as string
  const agentId = route.params.agent_id as string

  if (!tenantId.value) {
    toast.add({
      severity: 'error',
      summary: t('agent.configuration.saveError'),
      life: 5000,
    })
    return
  }

  try {
    await updateAgentInstance({
      agentClass,
      agentId,
      tenantId: tenantId.value,
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
