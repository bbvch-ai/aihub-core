import {
  type FormElement,
  type GroupConfig,
  type RepeaterConfig,
  buildFormKitSchema,
  categorizeFormElements,
  extractGroupConfigs,
  extractRepeaterConfigs,
  getNestedValue,
  hydrateFormData,
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
  /** Current locale ref for i18n-aware form rendering */
  locale: Ref<string>
}

/**
 * Shared form logic for creating agent/process instances from class definitions.
 *
 * Handles class selection, FormKit schema generation, stepper navigation, and form data
 * lifecycle. Hydration is shared with the edit form via `hydrateFormData` (and submission via
 * `serializeFormData`) so create and edit behave identically. Template/clone pre-filling is
 * done via applyInitialData(); domain-specific submission stays in the calling component.
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
    formData.value = newClass?.form && newClass.form.length > 0
      ? hydrateFormData({}, configForm.value as FormElement[])
      : {}
  }, { immediate: true })

  function applyInitialData(data: Record<string, unknown>) {
    // Hydrate from the template/clone data: nullable toggles follow the data's null-ness,
    // missing leaves fall back to their backend defaults — identical to the edit form.
    formData.value = hydrateFormData(data, configForm.value as FormElement[])
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
    applyInitialData,
    resetForm,
  }
}
