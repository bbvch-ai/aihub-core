<template>
  <Dialog
    v-model:visible="visible"
    modal
    :header="t('agent.create.title')"
    :style="{ width: '50rem' }"
    :closable="!isCreating"
  >
    <div class="flex flex-col gap-6">
      <div
        v-if="agentClassesAreLoading"
        class="flex items-center justify-center py-8"
      >
        <ProgressSpinner />
      </div>

      <div
        v-else-if="!agentClasses || agentClasses.length === 0"
        class="py-8 text-center text-surface-500"
      >
        {{ t('agent.create.noAgentClasses') }}
      </div>

      <template v-else>
        <div class="flex flex-col gap-2">
          <label
            for="agentClass"
            class="text-sm font-medium"
          >
            {{ t('agent.create.selectClass') }}
          </label>
          <Select
            v-model="selectedClass"
            :options="agentClasses"
            option-label="agent_class"
            option-value="agent_class"
            :placeholder="t('agent.create.selectClassPlaceholder')"
            class="w-full"
            :disabled="isCreating"
          />
        </div>

        <div class="flex flex-col gap-2">
          <label
            for="agentId"
            class="text-sm font-medium"
          >
            {{ t('agent.create.agentId') }}
          </label>
          <InputText
            v-model="agentId"
            :placeholder="t('agent.create.agentIdPlaceholder')"
            class="w-full"
            :invalid="!!agentIdError"
            :disabled="isCreating"
            @input="validateAgentId"
          />
          <small class="text-surface-500">
            {{ t('agent.create.agentIdHelp') }}
          </small>
          <small
            v-if="agentIdError"
            class="text-red-500"
          >
            {{ agentIdError }}
          </small>
        </div>

        <div
          v-if="selectedClassData && configForm.length > 0"
          class="flex flex-col gap-2"
        >
          <label class="text-sm font-medium">
            {{ t('agent.create.configuration') }}
          </label>
          <div class="max-h-96 overflow-y-auto rounded-lg border border-surface-200 p-4 dark:border-surface-700">
            <FormKit
              id="create-agent-form"
              v-model="formData"
              type="form"
              :actions="false"
              :config="{
                validationVisibility: 'blur',
              }"
            >
              <FormKitSchema
                :schema="schema"
                :data="formData"
              />

              <FormKitRepeater
                v-for="rep in repeaterElements"
                :key="rep.name"
                v-model="formData[rep.name] as Record<string, unknown>[]"
                :name="rep.name"
                :label="rep.label"
                :add-label="rep.addLabel"
                :children-schema="rep.childrenSchema"
                :min="rep.min"
                :max="rep.max"
              />
            </FormKit>
          </div>
        </div>
      </template>
    </div>

    <template #footer>
      <Button
        :label="t('agent.create.cancel')"
        severity="secondary"
        @click="closeModal"
      />
      <Button
        :label="t('agent.create.submit')"
        :disabled="!canSubmit || isCreating"
        :loading="isCreating"
        @click="handleSubmit"
      />
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import {
  type FormElement,
  type RepeaterConfig,
  buildFormKitSchema,
  extractRepeaterConfigs,
  getFormkitType,
} from '@core/composables/form/useFormKitTransform'

import type { AgentClassDto } from '@core/composables/agent/useAgentClasses'
import type { FormKitSchemaDefinition } from '@formkit/core'

const props = defineProps<{
  modelValue: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'success': [agentClass: string, agentId: string]
}>()

const { t, locale } = useI18n()
const toast = useToast()
const { agentClasses, agentClassesAreLoading } = useAgentClasses()
const { createAgent, isCreating } = useCreateAgent()

const selectedClass = ref<string>('')
const agentId = ref('')
const agentIdError = ref('')
const formData = ref<Record<string, unknown>>({})

const visible = computed({
  get: () => props.modelValue,
  set: (value: boolean) => emit('update:modelValue', value),
})

const selectedClassData = computed<AgentClassDto | undefined>(() => {
  if (!selectedClass.value || !agentClasses.value) return undefined
  return agentClasses.value.find(c => c.agent_class === selectedClass.value)
})

const configForm = computed(() => {
  return selectedClassData.value?.agent_config_specs?.form || []
})

const schema = computed<FormKitSchemaDefinition>(() => {
  return buildFormKitSchema(configForm.value as FormElement[], {
    locale: locale.value,
  })
})

const repeaterElements = computed<RepeaterConfig[]>(() => {
  return extractRepeaterConfigs(configForm.value as FormElement[], locale.value)
})

watch(selectedClassData, (newClass) => {
  if (newClass?.default_agent_config) {
    formData.value = initializeGroupData(
      configForm.value as FormElement[],
      { ...newClass.default_agent_config } as Record<string, unknown>,
    )
  }
  else {
    formData.value = {}
  }
}, { immediate: true })

function initializeElementData(
  element: FormElement,
  result: Record<string, unknown>,
  recursiveFn: (elements: FormElement[], data: Record<string, unknown>) => Record<string, unknown>,
): void {
  const formkitType = getFormkitType(element)
  const name = element.name as string
  const children = element.children as FormElement[] | undefined
  const hasChildren = children && Array.isArray(children)

  if (formkitType === 'group') {
    result[name] = result[name] ?? {}
    if (hasChildren) {
      result[name] = recursiveFn(children, result[name] as Record<string, unknown>)
    }
  }
  else if (formkitType === 'repeater') {
    result[name] = result[name] ?? []
    if (Array.isArray(result[name]) && hasChildren) {
      result[name] = (result[name] as Record<string, unknown>[]).map(item => recursiveFn(children, item))
    }
  }
}

function initializeGroupData(
  formElements: FormElement[],
  data: Record<string, unknown>,
): Record<string, unknown> {
  const result = { ...data }
  for (const element of formElements) {
    initializeElementData(element, result, initializeGroupData)
  }
  return result
}

const agentIdPattern = /^[a-z0-9_-]+$/

function validateAgentId() {
  if (!agentId.value) {
    agentIdError.value = ''
    return
  }

  if (!agentIdPattern.test(agentId.value)) {
    agentIdError.value = t('agent.create.agentIdInvalid')
  }
  else if (agentId.value.length > 100) {
    agentIdError.value = t('agent.create.agentIdTooLong')
  }
  else {
    agentIdError.value = ''
  }
}

const canSubmit = computed(() => {
  const hasClass = !!selectedClass.value
  const hasId = !!agentId.value
  const noError = !agentIdError.value
  const validPattern = agentIdPattern.test(agentId.value)

  return hasClass && hasId && noError && validPattern
})

function closeModal() {
  visible.value = false
  resetForm()
}

function resetForm() {
  selectedClass.value = ''
  agentId.value = ''
  agentIdError.value = ''
  formData.value = {}
}

async function handleSubmit() {
  if (!canSubmit.value) return

  try {
    await createAgent({
      request: {
        agent_class: selectedClass.value,
        agent_id: agentId.value,
        configuration: formData.value,
      },
    })

    toast.add({
      severity: 'success',
      summary: t('agent.create.success'),
      life: 3000,
    })

    emit('success', selectedClass.value, agentId.value)
    closeModal()
  }
  catch (error) {
    console.error('Failed to create agent:', error)
    toast.add({
      severity: 'error',
      summary: t('agent.create.error'),
      detail: error instanceof Error ? error.message : String(error),
      life: 5000,
    })
  }
}
</script>
