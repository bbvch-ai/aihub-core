import { merge } from 'lodash-es'

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

/**
 * Drops keys whose matching form-schema node is a group/repeater and whose incoming
 * value is `null`. FormKit rejects `null` for group values (must be an object) and for
 * repeater values (must be an array), so template payloads that serialise optional
 * nested configs as `null` (Pydantic `Form | None = None`) would otherwise throw during
 * hydration.
 */
export function stripNullsForGroups(
  data: Record<string, unknown>,
  elements: FormElement[],
): Record<string, unknown> {
  const result: Record<string, unknown> = {}

  for (const [key, value] of Object.entries(data)) {
    const element = elements.find(el => el.name === key)
    if (!element) {
      result[key] = value
      continue
    }
    const formkitType = getFormkitType(element)

    if ((formkitType === 'group' || formkitType === 'repeater') && value === null) {
      continue
    }

    const children = (element.children as FormElement[] | undefined) ?? []

    if (formkitType === 'group' && value && typeof value === 'object' && !Array.isArray(value)) {
      result[key] = stripNullsForGroups(value as Record<string, unknown>, children)
    }
    else if (formkitType === 'repeater' && Array.isArray(value)) {
      result[key] = value.map(item =>
        item && typeof item === 'object' && !Array.isArray(item)
          ? stripNullsForGroups(item as Record<string, unknown>, children)
          : item,
      )
    }
    else {
      result[key] = value
    }
  }

  return result
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
  /** Current locale ref for i18n-aware form rendering */
  locale: Ref<string>
}

/**
 * Shared form logic for creating agent/process instances from class definitions.
 *
 * Handles class selection, FormKit schema generation, stepper navigation,
 * and form data lifecycle. Template/clone pre-filling is done via applyInitialData().
 * Domain-specific submission logic stays in the calling component.
 */
export function useCreateInstanceForm<T extends ClassDataLike>(options: CreateInstanceFormOptions<T>) {
  const { classes, classField, initialClass, locale } = options

  const selectedClass = ref<string>(initialClass())
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

  function applyInitialData(data: Record<string, unknown>) {
    const base = initializeGroupData(configForm.value as FormElement[], {})
    const sanitized = stripNullsForGroups(data, configForm.value as FormElement[])
    formData.value = merge(base, sanitized)
  }

  function resetForm() {
    selectedClass.value = initialClass()
    formData.value = {}
    activeStep.value = 0
  }

  return {
    selectedClass,
    formData,
    activeStep,
    selectedClassData,
    configForm,
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
    applyInitialData,
    resetForm,
  }
}
