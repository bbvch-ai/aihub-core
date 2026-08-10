<template>
  <StructuralColumn
    :title="t('process.configuration.title')"
    close-route="/service/processes"
    :loading="processInstanceIsLoading"
    size="normal"
  >
    <div class="flex flex-col gap-3">
      <p class="mb-4 text-sm text-surface-500 dark:text-surface-400">
        {{ t('process.configuration.description') }}
      </p>
      <ProcessConfiguration
        v-if="configForm && configForm.length > 0 && !processInstanceIsLoading"
        :title="t('process.configuration.runtimeSettings')"
        :description="processInstance?.process_config.description || ''"
        :form="configForm"
        :initial-data="configurationData"
        @submit="submitConfiguration"
      />
      <div
        v-else-if="processInstanceIsLoading"
        class="text-center text-sm text-surface-500 dark:text-surface-400"
      >
        {{ t('common.loading') }}
      </div>
      <div
        v-else
        class="text-center text-sm text-surface-500 dark:text-surface-400"
      >
        {{ t('process.configuration.noConfiguration') }}
      </div>
    </div>
  </StructuralColumn>
</template>

<script setup lang="ts">
import type { FullProcessInstanceDtoReadable } from '@core/sdk/client'

type FormElement = FullProcessInstanceDtoReadable['form'][number]

const route = useRoute()
const { processInstance, processInstanceIsLoading } = useProcessInstance()
const { updateProcessInstance } = useUpdateProcessInstance()
const { t } = useI18n()
const toast = useToast()

const configForm = computed(() => processInstance.value?.form || [])

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
  const rawData = (processInstance.value?.configuration || {}) as Record<string, unknown>
  return initializeGroupData(configForm.value, rawData)
})

const submitConfiguration = async (formData: Record<string, unknown>) => {
  const processClass = route.params.process_class as string
  const processId = route.params.process_id as string

  try {
    await updateProcessInstance({
      processClass,
      processId,
      configuration: formData,
    })
    toast.add({
      severity: 'success',
      summary: t('process.configuration.saveSuccess'),
      life: 3000,
    })
  }
  catch (error) {
    console.error('Failed to save process configuration:', error)
    toast.add({
      severity: 'error',
      summary: t('process.configuration.saveError'),
      detail: error instanceof Error ? error.message : String(error),
      life: 5000,
    })
  }
}
</script>
