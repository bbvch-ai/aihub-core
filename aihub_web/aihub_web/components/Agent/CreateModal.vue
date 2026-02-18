<template>
  <Dialog
    v-model:visible="visible"
    modal
    :header="t('agent.create.title')"
    :style="{ width: '50rem' }"
    :closable="!isSubmitting"
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
        <div
          v-if="!hasFixedClass"
          class="flex flex-col gap-2"
        >
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
            :disabled="isSubmitting"
          />
        </div>

        <div
          v-if="templateOptions.length > 0"
          class="flex flex-col gap-2"
        >
          <label class="text-sm font-medium">
            {{ t('agent.create.selectTemplate') }}
          </label>
          <Select
            v-model="selectedTemplate"
            :options="templateOptions"
            option-label="label"
            option-value="value"
            :placeholder="t('agent.create.selectTemplatePlaceholder')"
            class="w-full"
            :disabled="isSubmitting"
          />
        </div>

        <div
          v-if="selectedClassData && configForm.length > 0"
          class="content flex flex-col gap-2"
        >
          <FormKit
            id="create-agent-form"
            v-model="formData"
            type="form"
            :actions="false"
            :config="{
              validationVisibility: 'dirty',
            }"
            @submit="handleFormSubmit"
            @submit-invalid="isSubmitting = false"
          >
            <Stepper
              v-model:value="activeStep"
              orientation="vertical"
            >
              <StepItem
                v-if="simpleElementsSchema.length > 0"
                :value="0"
              >
                <Step>{{ t('agent.create.steps.basicInfo') }}</Step>
                <StepPanel>
                  <div class="flex flex-col gap-6 py-4">
                    <FormKitSchema
                      :schema="simpleElementsSchema"
                      :data="formData"
                    />
                  </div>
                </StepPanel>
              </StepItem>
              <StepItem
                v-for="(group, index) in groupConfigs"
                :key="`group-${group.name}`"
                :value="getGroupStepIndex(index)"
              >
                <Step>{{ group.label || group.name }}</Step>
                <StepPanel>
                  <div class="content py-4">
                    <FormKitSchema
                      :schema="group.schema"
                      :data="formData"
                    />
                  </div>
                </StepPanel>
              </StepItem>
              <StepItem
                v-for="(rep, index) in repeaterConfigs"
                :key="`repeater-${rep.path}`"
                :value="getRepeaterStepIndex(index)"
              >
                <Step>{{ rep.label || rep.name }}</Step>
                <StepPanel>
                  <div class="py-4">
                    <FormKitRepeater
                      :model-value="getRepeaterData(rep.path)"
                      :name="rep.name"
                      :label="rep.label"
                      :add-label="rep.addLabel"
                      :children-schema="rep.childrenSchema"
                      :min="rep.min"
                      :max="rep.max"
                      @update:model-value="setRepeaterData(rep.path, $event)"
                    />
                  </div>
                </StepPanel>
              </StepItem>
            </Stepper>
          </FormKit>
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
        :disabled="!selectedClass || isSubmitting"
        :loading="isSubmitting"
        @click="triggerFormSubmit"
      />
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import {
  type FormElement,
  type GroupConfig,
  type RepeaterConfig,
  buildFormKitSchema,
  categorizeFormElements,
  extractGroupConfigs,
  extractRepeaterConfigs,
  getFormkitType,
  getNestedValue,
  normalizeFormLocaleStrings,
  setNestedValue,
} from '@core/composables/form/useFormKitTransform'
import { getNode } from '@formkit/core'
import merge from 'lodash/merge'

import type { AgentClassDto } from '@core/composables/agent/useAgentClasses'
import type { FormKitSchemaNode } from '@formkit/core'

const props = defineProps<{
  modelValue: boolean
  initialClass?: string
  initialTemplate?: number | null
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'success': [agentClass: string, agentId: string]
}>()

const { t, locale } = useI18n()
const toast = useToast()
const { agentClasses, agentClassesAreLoading } = useAgentClasses()
const { createAgentInstance } = useCreateAgentInstance()

const selectedClass = ref<string>(props.initialClass ?? '')
const selectedTemplate = ref<number | null>(null)
const formData = ref<Record<string, unknown>>({})
const activeStep = ref(0)
const isSubmitting = ref(false)

const hasFixedClass = computed(() => !!props.initialClass)

watch(() => props.initialClass, (newClass) => {
  if (newClass) {
    selectedClass.value = newClass
  }
})

const visible = computed({
  get: () => props.modelValue,
  set: (value: boolean) => emit('update:modelValue', value),
})

// Ordering dependency: the selectedClassData watcher (below) resets selectedTemplate to null
// whenever the selected class changes. When the modal opens with a preselected template, we
// must wait for that reset to complete before applying initialTemplate, hence nextTick.
watch(visible, (isVisible) => {
  if (isVisible && props.initialTemplate !== undefined && props.initialTemplate !== null) {
    nextTick(() => {
      selectedTemplate.value = props.initialTemplate!
    })
  }
})

const selectedClassData = computed<AgentClassDto | undefined>(() => {
  if (!selectedClass.value || !agentClasses.value) return undefined
  return agentClasses.value.find(c => c.agent_class === selectedClass.value)
})

const configForm = computed(() => {
  return selectedClassData.value?.form || []
})

const availableTemplates = computed(() => {
  return selectedClassData.value?.templates ?? []
})

const templateOptions = computed(() => {
  if (availableTemplates.value.length === 0) return []
  const options = availableTemplates.value.map((template, index) => {
    const name = template.name as Record<string, string> | undefined
    const label = name?.[locale.value] ?? name?.en ?? template.agent_id as string ?? `Template ${index + 1}`
    return { label, value: index }
  })
  return [{ label: t('agent.create.startFromScratch'), value: -1 }, ...options]
})

watch(selectedTemplate, (index) => {
  if (index === null || index === -1) {
    // Reset to default form data (FormKit defaults from elements)
    formData.value = initializeGroupData(configForm.value as FormElement[], {})
    return
  }
  const template = availableTemplates.value[index]
  if (template) {
    const base = initializeGroupData(configForm.value as FormElement[], {})
    formData.value = merge(base, template)
  }
})

const categorizedElements = computed(() => {
  return categorizeFormElements(configForm.value as FormElement[])
})

const simpleElementsSchema = computed<FormKitSchemaNode[]>(() => {
  return buildFormKitSchema(categorizedElements.value.simpleElements, {
    locale: locale.value,
  })
})

const groupConfigs = computed<GroupConfig[]>(() => {
  return extractGroupConfigs(configForm.value as FormElement[], locale.value)
})

const repeaterConfigs = computed<RepeaterConfig[]>(() => {
  return extractRepeaterConfigs(configForm.value as FormElement[], locale.value)
})

function getRepeaterData(path: string): Record<string, unknown>[] {
  return getNestedValue(formData.value, path)
}

function setRepeaterData(path: string, value: Record<string, unknown>[]): void {
  setNestedValue(formData.value, path, value)
}

const hasSimpleElements = computed(() => simpleElementsSchema.value.length > 0)

function getGroupStepIndex(groupIndex: number): number {
  return (hasSimpleElements.value ? 1 : 0) + groupIndex
}

function getRepeaterStepIndex(repeaterIndex: number): number {
  return (hasSimpleElements.value ? 1 : 0) + groupConfigs.value.length + repeaterIndex
}

watch(selectedClassData, (newClass) => {
  selectedTemplate.value = null
  if (newClass?.form && newClass.form.length > 0) {
    // Initialize form data with proper structure for groups/repeaters
    // Default values are embedded in the FormKit elements themselves
    formData.value = initializeGroupData(configForm.value as FormElement[], {})
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

function closeModal() {
  visible.value = false
  resetForm()
}

function resetForm() {
  selectedClass.value = props.initialClass ?? ''
  selectedTemplate.value = props.initialTemplate ?? null
  formData.value = {}
  activeStep.value = 0
}

function triggerFormSubmit() {
  isSubmitting.value = true
  const formNode = getNode('create-agent-form')
  if (formNode) {
    formNode.submit()
  }
  else {
    handleFormSubmit()
  }
}

function cleanFormData(data: Record<string, unknown>): Record<string, unknown> {
  const result: Record<string, unknown> = {}
  // FormKit artifacts that should be stripped from submissions
  const formkitArtifacts = new Set(['slots'])

  for (const [key, value] of Object.entries(data)) {
    // Skip FormKit artifacts
    if (formkitArtifacts.has(key)) continue

    // Recursively clean nested objects
    if (value !== null && typeof value === 'object' && !Array.isArray(value)) {
      result[key] = cleanFormData(value as Record<string, unknown>)
    }
    else {
      result[key] = value
    }
  }

  return result
}

async function handleFormSubmit() {
  // This function is only called by FormKit when all validation passes
  try {
    const cleanedData = cleanFormData(formData.value)
    const normalizedConfig = normalizeFormLocaleStrings(cleanedData)
    const agentId = normalizedConfig.agent_id as string
    await createAgentInstance({
      agentClass: selectedClass.value,
      request: {
        agent_id: agentId,
        configuration: normalizedConfig,
      },
    })

    toast.add({
      severity: 'success',
      summary: t('agent.create.success'),
      life: 3000,
    })

    emit('success', selectedClass.value, agentId)
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
  finally {
    isSubmitting.value = false
  }
}
</script>

<style scoped>
.content {
  @apply font-light text-xs
}

.content :deep(.formkit-group-fieldset) {
  @apply flex flex-col gap-6;
}

.content :deep(.formkit-outer) {
  @apply pt-3 pb-1;
}

.content :deep(.formkit-group-fieldset) {
}

.content :deep(.formkit-group-fieldset legend) {
  @apply hidden;
}

.content :deep(.formkit-group-fieldset .formkit-group-fieldset) {
}

.content :deep(.formkit-slider-value-input) {
  @apply w-20;
}

.content :deep(.formkit-slider-value-input .p-inputnumber-input) {
  @apply text-center text-sm;
}

.content :deep(#create-agent-form-incomplete) {
  @apply font-bold text-sm text-right pr-2;
}
</style>
