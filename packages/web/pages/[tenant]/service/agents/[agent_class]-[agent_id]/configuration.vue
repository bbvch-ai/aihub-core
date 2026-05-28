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
import type { AgentConfigDtoReadable } from '@core/sdk/client'

type FormElement = NonNullable<AgentConfigDtoReadable['form']>[number]

const route = useRoute()
const { tenantId } = useTenant()
const { agentInstance, agentInstanceIsLoading } = useAgentInstance()
const { updateAgentInstance } = useUpdateAgentInstance()
const { t } = useI18n()
const toast = useToast()

const configForm = computed(() => agentInstance.value?.agent_config?.form || [])

/**
 * Recursively initializes nested Group values with empty objects based on form schema.
 * FormKit Groups require object values - they cannot be null or undefined.
 * This ensures all Group elements have at least an empty object as their value.
 */
const initializeGroupData = (
  formElements: FormElement[],
  data: Record<string, unknown>,
): Record<string, unknown> => {
  const result = { ...data }

  for (const element of formElements) {
    const elementRecord = element as Record<string, unknown>
    const formkitType = elementRecord.formkit || elementRecord.$formkit

    if (formkitType === 'group') {
      const name = elementRecord.name as string
      const children = elementRecord.children as FormElement[] | undefined

      if (result[name] === null || result[name] === undefined) {
        result[name] = {}
      }

      if (children && Array.isArray(children)) {
        result[name] = initializeGroupData(children, result[name] as Record<string, unknown>)
      }
    }
  }

  return result
}

const configurationData = computed(() => {
  const rawData = (agentInstance.value?.configuration || {}) as Record<string, unknown>
  return initializeGroupData(configForm.value, rawData)
})

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
