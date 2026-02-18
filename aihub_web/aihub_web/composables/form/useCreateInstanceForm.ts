import merge from 'lodash/merge'

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
  setNestedValue,
} from './useFormKitTransform'

import type { FormKitSchemaNode } from '@formkit/core'
import type { Ref } from 'vue'

export interface ClassDataLike {
  form: unknown[]
  templates?: Array<Record<string, unknown>>
}

export interface CreateInstanceFormOptions<T extends ClassDataLike> {
  /** Reactive list of available class definitions (agent classes, process classes, etc.) */
  classes: Ref<T[] | undefined>
  /** Property name used to identify a class (e.g. 'agent_class', 'process_class') */
  classField: string
  /** Property name used as fallback label in templates (e.g. 'agent_id', 'process_id') */
  idField: string
  /** Getter for the initial class selection (from component props) */
  initialClass: () => string
  /** Getter for the initial template index (from component props) */
  initialTemplate: () => number | null
  /** Reactive translated label for the "start from scratch" template option */
  startFromScratchLabel: Ref<string>
  /** Current locale ref for i18n-aware form rendering */
  locale: Ref<string>
}

/**
 * Shared form logic for creating agent/process instances from class definitions.
 *
 * Handles class selection, template application, FormKit schema generation,
 * stepper navigation, and form data lifecycle. Domain-specific submission
 * logic stays in the calling component.
 */
export function useCreateInstanceForm<T extends ClassDataLike>(options: CreateInstanceFormOptions<T>) {
  const { classes, classField, idField, initialClass, initialTemplate, startFromScratchLabel, locale } = options

  const selectedClass = ref<string>(initialClass())
  const selectedTemplate = ref<number | null>(null)
  const formData = ref<Record<string, unknown>>({})
  const activeStep = ref(0)

  watch(initialClass, (newClass) => {
    if (newClass) {
      selectedClass.value = newClass
    }
  })

  const selectedClassData = computed<T | undefined>(() => {
    if (!selectedClass.value || !classes.value) return undefined
    return classes.value.find(c => c[classField as keyof T] === selectedClass.value)
  })

  const configForm = computed(() => selectedClassData.value?.form ?? [])

  const availableTemplates = computed(() => selectedClassData.value?.templates ?? [])

  const templateOptions = computed(() => {
    if (availableTemplates.value.length === 0) return []
    const mapped = availableTemplates.value.map((template, index) => {
      const name = template.name as Record<string, string> | undefined
      const label = name?.[locale.value] ?? name?.en ?? template[idField] as string ?? `Template ${index + 1}`
      return { label, value: index }
    })
    return [{ label: startFromScratchLabel.value, value: -1 }, ...mapped]
  })

  watch(selectedTemplate, (index) => {
    if (index === null || index === -1) {
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
    return buildFormKitSchema(categorizedElements.value.simpleElements, { locale: locale.value })
  })

  const groupConfigs = computed<GroupConfig[]>(() => {
    return extractGroupConfigs(configForm.value as FormElement[], locale.value)
  })

  const repeaterConfigs = computed<RepeaterConfig[]>(() => {
    return extractRepeaterConfigs(configForm.value as FormElement[], locale.value)
  })

  const hasSimpleElements = computed(() => simpleElementsSchema.value.length > 0)

  function getGroupStepIndex(groupIndex: number): number {
    return (hasSimpleElements.value ? 1 : 0) + groupIndex
  }

  function getRepeaterStepIndex(repeaterIndex: number): number {
    return (hasSimpleElements.value ? 1 : 0) + groupConfigs.value.length + repeaterIndex
  }

  function getRepeaterData(path: string): Record<string, unknown>[] {
    return getNestedValue(formData.value, path)
  }

  function setRepeaterData(path: string, value: Record<string, unknown>[]): void {
    setNestedValue(formData.value, path, value)
  }

  watch(selectedClassData, (newClass) => {
    selectedTemplate.value = null
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

  function cleanFormData(data: Record<string, unknown>): Record<string, unknown> {
    const result: Record<string, unknown> = {}
    // FormKit artifacts that should be stripped from submissions
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

  function resetForm() {
    selectedClass.value = initialClass()
    selectedTemplate.value = initialTemplate()
    formData.value = {}
    activeStep.value = 0
  }

  return {
    selectedClass,
    selectedTemplate,
    formData,
    activeStep,
    selectedClassData,
    configForm,
    templateOptions,
    categorizedElements,
    simpleElementsSchema,
    groupConfigs,
    repeaterConfigs,
    hasSimpleElements,
    getGroupStepIndex,
    getRepeaterStepIndex,
    getRepeaterData,
    setRepeaterData,
    initializeGroupData,
    cleanFormData,
    resetForm,
  }
}
