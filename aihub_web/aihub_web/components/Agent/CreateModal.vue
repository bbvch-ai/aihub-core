<template>
  <Dialog
    v-model:visible="visible"
    modal
    :header="t('agent.create.title')"
    :style="{ width: '50rem' }"
    :closable="!isCreating"
  >
    <div class="flex flex-col gap-6">
      <!-- Loading state -->
      <div
        v-if="agentClassesAreLoading"
        class="flex items-center justify-center py-8"
      >
        <ProgressSpinner />
      </div>

      <!-- No agent classes available -->
      <div
        v-else-if="!agentClasses || agentClasses.length === 0"
        class="py-8 text-center text-surface-500"
      >
        {{ t('agent.create.noAgentClasses') }}
      </div>

      <!-- Form content -->
      <template v-else>
        <!-- Step 1: Select Agent Class -->
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

        <!-- Step 2: Enter Agent ID -->
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

        <!-- Step 3: Configuration Form -->
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

              <!-- Render repeaters separately (not supported by FormKit standard) -->
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

    <!-- Footer with action buttons -->
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
import type { AgentClassDto } from '@core/composables/agent/useAgentClasses'
import type { FormKitSchemaDefinition, FormKitSchemaNode } from '@formkit/core'

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

// Form state
const selectedClass = ref<string>('')
const agentId = ref('')
const agentIdError = ref('')
const formData = ref<Record<string, unknown>>({})

// Computed visibility for v-model
const visible = computed({
  get: () => props.modelValue,
  set: (value: boolean) => emit('update:modelValue', value),
})

// Get the selected class data
const selectedClassData = computed<AgentClassDto | undefined>(() => {
  if (!selectedClass.value || !agentClasses.value) return undefined
  return agentClasses.value.find(c => c.agent_class === selectedClass.value)
})

// Get the form schema from selected class
const configForm = computed(() => {
  return selectedClassData.value?.agent_config_specs?.form || []
})

// Transform form elements to FormKit schema
type FormElement = Record<string, unknown>

// Helper to get localized string value
function getLocalizedString(value: unknown, currentLocale: string): string | undefined {
  if (!value) return undefined
  if (typeof value === 'string') return value
  if (typeof value === 'object' && value !== null) {
    const localeObj = value as Record<string, string>
    return localeObj[currentLocale] || localeObj.en || Object.values(localeObj)[0]
  }
  return String(value)
}

// Wraps a node in a labeled fieldset
function wrapInFieldset(label: string, node: FormKitSchemaNode): FormKitSchemaNode[] {
  return [{
    $el: 'fieldset',
    attrs: { class: 'border border-surface-300 dark:border-surface-600 rounded-lg p-4 mb-4' },
    children: [
      {
        $el: 'legend',
        attrs: { class: 'text-sm font-semibold px-2 text-surface-700 dark:text-surface-300' },
        children: label,
      },
      node,
    ],
  }] as FormKitSchemaNode[]
}

// Repeater element configuration for custom rendering
interface RepeaterConfig {
  name: string
  label?: string
  addLabel?: string
  childrenSchema: FormKitSchemaNode[]
  min?: number
  max?: number
}

const schema = computed<FormKitSchemaDefinition>(() => {
  if (!configForm.value || configForm.value.length === 0) return []

  const currentLocale = locale.value

  function transformElement(formElement: FormElement): FormKitSchemaNode | FormKitSchemaNode[] {
    if (!formElement) return []

    const formkitType = formElement.formkit || formElement.$formkit

    // Skip repeaters - they're rendered separately with custom component
    if (formkitType === 'repeater') return []

    const children = (formElement.children as FormElement[] || []).flatMap(transformElement)
    const label = getLocalizedString(formElement.label, currentLocale)

    // Handle group elements
    if (formkitType === 'group') {
      const groupNode: FormKitSchemaNode = {
        $formkit: 'group',
        name: formElement.name as string,
        children: children as FormKitSchemaNode[],
      }
      return label ? wrapInFieldset(label, groupNode) : groupNode
    }

    // Build a clean node for other element types
    const cleanNode: Record<string, unknown> = { $formkit: formkitType }
    if (formElement.name) cleanNode.name = formElement.name
    if (label) cleanNode.label = label
    const help = getLocalizedString(formElement.help, currentLocale)
    if (help) cleanNode.help = help
    const placeholder = getLocalizedString(formElement.placeholder, currentLocale)
    if (placeholder) cleanNode.placeholder = placeholder
    if (formElement.validation) cleanNode.validation = formElement.validation
    if (formElement.options) cleanNode.options = formElement.options
    if (formElement.value !== undefined) cleanNode.value = formElement.value
    if (children.length > 0) cleanNode.children = children

    return cleanNode as FormKitSchemaNode
  }

  try {
    return configForm.value.flatMap(el => transformElement(el as FormElement))
  }
  catch (error) {
    console.error('Error transforming schema:', error)
    return []
  }
})

// Extract repeater elements for custom rendering
const repeaterElements = computed<RepeaterConfig[]>(() => {
  if (!configForm.value || configForm.value.length === 0) return []

  const currentLocale = locale.value
  const repeaters: RepeaterConfig[] = []

  function transformChildElement(formElement: FormElement): FormKitSchemaNode | FormKitSchemaNode[] {
    if (!formElement) return []
    const formkitType = formElement.formkit || formElement.$formkit
    const children = (formElement.children as FormElement[] || []).flatMap(transformChildElement)
    const label = getLocalizedString(formElement.label, currentLocale)

    if (formkitType === 'group') {
      const groupNode: FormKitSchemaNode = {
        $formkit: 'group',
        name: formElement.name as string,
        children: children as FormKitSchemaNode[],
      }
      return label ? wrapInFieldset(label, groupNode) : groupNode
    }

    const cleanNode: Record<string, unknown> = { $formkit: formkitType }
    if (formElement.name) cleanNode.name = formElement.name
    if (label) cleanNode.label = label
    const help = getLocalizedString(formElement.help, currentLocale)
    if (help) cleanNode.help = help
    if (formElement.validation) cleanNode.validation = formElement.validation
    if (formElement.options) cleanNode.options = formElement.options
    if (children.length > 0) cleanNode.children = children

    return cleanNode as FormKitSchemaNode
  }

  for (const el of configForm.value) {
    const element = el as FormElement
    const formkitType = element.formkit || element.$formkit
    if (formkitType === 'repeater') {
      const childrenSchema = (element.children as FormElement[] || []).flatMap(transformChildElement)
      repeaters.push({
        name: element.name as string,
        label: getLocalizedString(element.label, currentLocale),
        addLabel: getLocalizedString(element.addLabel || element.add_label, currentLocale),
        childrenSchema: childrenSchema as FormKitSchemaNode[],
        min: element.min as number | undefined,
        max: element.max as number | undefined,
      })
    }
  }

  return repeaters
})

// Initialize form data when class is selected
watch(selectedClassData, (newClass) => {
  if (newClass?.default_agent_config) {
    // Initialize with default config, ensuring nested groups have objects
    formData.value = initializeGroupData(
      configForm.value as FormElement[],
      { ...newClass.default_agent_config } as Record<string, unknown>,
    )
  }
  else {
    formData.value = {}
  }
}, { immediate: true })

// Initialize a single element's data based on its type
function initializeElementData(
  element: FormElement,
  result: Record<string, unknown>,
  recursiveFn: (elements: FormElement[], data: Record<string, unknown>) => Record<string, unknown>,
): void {
  const formkitType = element.formkit || element.$formkit
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

// Helper to initialize group and repeater data with proper structures
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

// Validate agent ID
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

// Can submit check
const canSubmit = computed(() => {
  const hasClass = !!selectedClass.value
  const hasId = !!agentId.value
  const noError = !agentIdError.value
  const validPattern = agentIdPattern.test(agentId.value)

  return hasClass && hasId && noError && validPattern
})

// Close modal
function closeModal() {
  visible.value = false
  resetForm()
}

// Reset form
function resetForm() {
  selectedClass.value = ''
  agentId.value = ''
  agentIdError.value = ''
  formData.value = {}
}

// Handle submit
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
