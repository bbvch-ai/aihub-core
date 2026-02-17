<template>
  <Dialog
    v-model:visible="visible"
    modal
    :header="t('process.create.title')"
    :style="{ width: '50rem' }"
    :closable="!isCreating"
  >
    <div class="flex flex-col gap-6">
      <div
        v-if="processClassesAreLoading"
        class="flex items-center justify-center py-8"
      >
        <ProgressSpinner />
      </div>

      <div
        v-else-if="!processClasses || processClasses.length === 0"
        class="py-8 text-center text-surface-500"
      >
        {{ t('process.create.noProcessClasses') }}
      </div>

      <template v-else>
        <div
          v-if="!hasFixedClass"
          class="flex flex-col gap-2"
        >
          <label
            for="processClass"
            class="text-sm font-medium"
          >
            {{ t('process.create.selectClass') }}
          </label>
          <Select
            v-model="selectedClass"
            :options="processClasses"
            option-label="process_class"
            option-value="process_class"
            :placeholder="t('process.create.selectClassPlaceholder')"
            class="w-full"
            :disabled="isCreating"
          />
        </div>

        <div
          v-if="selectedClassData && configForm.length > 0"
          class="content flex flex-col gap-2"
        >
          <FormKit
            id="create-process-form"
            v-model="formData"
            type="form"
            :actions="false"
            :config="{
              validationVisibility: 'dirty',
            }"
            @submit="handleFormSubmit"
          >
            <Stepper
              v-model:value="activeStep"
              orientation="vertical"
            >
              <StepItem
                v-if="simpleElementsSchema.length > 0"
                :value="0"
              >
                <Step>{{ t('process.create.steps.basicInfo') }}</Step>
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
        :label="t('process.create.cancel')"
        severity="secondary"
        @click="closeModal"
      />
      <Button
        :label="t('process.create.submit')"
        :disabled="!selectedClass || isCreating"
        :loading="isCreating"
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

import type { ProcessClassDto } from '@core/composables/process/useProcessClasses'
import type { FormKitSchemaNode } from '@formkit/core'

const props = defineProps<{
  modelValue: boolean
  initialClass?: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'success': [processClass: string, processId: string]
}>()

const { t, locale } = useI18n()
const toast = useToast()
const { processClasses, processClassesAreLoading } = useProcessClasses()
const { createProcessInstance, isCreating } = useCreateProcessInstance()

const selectedClass = ref<string>(props.initialClass ?? '')
const formData = ref<Record<string, unknown>>({})
const activeStep = ref(0)

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

const selectedClassData = computed<ProcessClassDto | undefined>(() => {
  if (!selectedClass.value || !processClasses.value) return undefined
  return processClasses.value.find(c => c.process_class === selectedClass.value)
})

const configForm = computed(() => {
  return selectedClassData.value?.form || []
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
  if (newClass?.form && newClass.form.length > 0) {
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
  formData.value = {}
  activeStep.value = 0
}

function triggerFormSubmit() {
  const formNode = getNode('create-process-form')
  if (formNode) {
    formNode.submit()
  }
}

function cleanFormData(data: Record<string, unknown>): Record<string, unknown> {
  const result: Record<string, unknown> = {}
  const formkitArtifacts = new Set(['slots'])

  for (const [key, value] of Object.entries(data)) {
    if (formkitArtifacts.has(key)) continue

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
  try {
    const cleanedData = cleanFormData(formData.value)
    const normalizedConfig = normalizeFormLocaleStrings(cleanedData)
    const processId = normalizedConfig.process_id as string
    await createProcessInstance({
      processClass: selectedClass.value,
      request: {
        process_id: processId,
        configuration: normalizedConfig,
      },
    })

    toast.add({
      severity: 'success',
      summary: t('process.create.success'),
      life: 3000,
    })

    emit('success', selectedClass.value, processId)
    closeModal()
  }
  catch (error) {
    console.error('Failed to create process:', error)
    toast.add({
      severity: 'error',
      summary: t('process.create.error'),
      detail: error instanceof Error ? error.message : String(error),
      life: 5000,
    })
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

.content :deep(#create-process-form-incomplete) {
  @apply font-bold text-sm text-right pr-2;
}
</style>
