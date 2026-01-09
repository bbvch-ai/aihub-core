import type { FormKitSchemaNode } from '@formkit/core'

export interface RepeaterConfig {
  name: string
  label?: string
  addLabel?: string
  childrenSchema: FormKitSchemaNode[]
  min?: number
  max?: number
}

export type FormElement = Record<string, unknown>

/**
 * Gets the FormKit type from an element, checking both 'formkit' and '$formkit' properties.
 */
export function getFormkitType(element: FormElement): unknown {
  return element.formkit || element.$formkit
}

/**
 * Wraps a FormKit schema node in a fieldset with a legend label.
 */
export function wrapInFieldset(label: string, node: FormKitSchemaNode): FormKitSchemaNode[] {
  return [{
    $el: 'fieldset',
    attrs: { class: 'formkit-group-fieldset border border-surface-300 dark:border-surface-600 rounded-lg p-4 mb-4' },
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

/**
 * Gets a localized string from a value that may be a string or a locale object.
 */
export function getLocalizedString(value: unknown, locale: string): string | undefined {
  if (!value) return undefined
  if (typeof value === 'string') return value
  if (typeof value === 'object') {
    const localeObj = value as Record<string, string>
    return localeObj[locale] || localeObj.en || Object.values(localeObj)[0]
  }
  return String(value)
}

export interface TransformOptions {
  locale?: string
  labelTransform?: (label: string) => string
  optionsResolver?: (element: FormElement) => unknown[] | undefined
}

function createGroupNode(
  element: FormElement,
  children: FormKitSchemaNode[],
  label: string | undefined,
): FormKitSchemaNode | FormKitSchemaNode[] {
  const groupNode: FormKitSchemaNode = {
    $formkit: 'group',
    name: element.name as string,
    children,
  }
  return label ? wrapInFieldset(label, groupNode) : groupNode
}

function resolveElementOptions(
  element: FormElement,
  optionsResolver?: (element: FormElement) => unknown[] | undefined,
): unknown[] | undefined {
  if (optionsResolver) {
    return optionsResolver(element)
  }
  return element.options as unknown[] | undefined
}

function buildNodeProperties(
  element: FormElement,
  formkitType: unknown,
  label: string | undefined,
  locale: string,
  optionsResolver?: (element: FormElement) => unknown[] | undefined,
): Record<string, unknown> {
  const cleanNode: Record<string, unknown> = { $formkit: formkitType }

  if (element.name) cleanNode.name = element.name
  if (label) cleanNode.label = label

  const help = getLocalizedString(element.help, locale)
  if (help) cleanNode.help = help

  const placeholder = getLocalizedString(element.placeholder, locale)
  if (placeholder) cleanNode.placeholder = placeholder

  if (element.validation) cleanNode.validation = element.validation
  if (element.value !== undefined) cleanNode.value = element.value

  const options = resolveElementOptions(element, optionsResolver)
  if (options) cleanNode.options = options

  return cleanNode
}

/**
 * Transforms a form element to a FormKit schema node.
 * Handles groups specially by wrapping them in fieldsets when they have labels.
 * Skips repeater elements (they are handled separately).
 */
export function transformElementToSchema(
  element: FormElement,
  options: TransformOptions = {},
): FormKitSchemaNode | FormKitSchemaNode[] {
  if (!element) return []

  const formkitType = getFormkitType(element)
  if (formkitType === 'repeater') return []

  const { locale = 'en', labelTransform, optionsResolver } = options

  const children = (element.children as FormElement[] || []).flatMap(
    child => transformElementToSchema(child, options),
  ) as FormKitSchemaNode[]

  let label = getLocalizedString(element.label, locale)
  if (label && labelTransform) {
    label = labelTransform(label)
  }

  if (formkitType === 'group') {
    return createGroupNode(element, children, label)
  }

  const cleanNode = buildNodeProperties(element, formkitType, label, locale, optionsResolver)
  if (children.length > 0) cleanNode.children = children

  return cleanNode as FormKitSchemaNode
}

/**
 * Transforms a form element for use inside a repeater's children schema.
 */
export function transformElementForRepeater(
  element: FormElement,
  locale = 'en',
): FormKitSchemaNode | FormKitSchemaNode[] {
  if (!element) return []

  const formkitType = getFormkitType(element)
  const children = (element.children as FormElement[] || []).flatMap(
    child => transformElementForRepeater(child, locale),
  ) as FormKitSchemaNode[]

  const label = getLocalizedString(element.label, locale)

  if (formkitType === 'group') {
    return createGroupNode(element, children, label)
  }

  const cleanNode: Record<string, unknown> = { $formkit: formkitType }

  if (element.name) cleanNode.name = element.name
  if (label) cleanNode.label = label

  const help = getLocalizedString(element.help, locale)
  if (help) cleanNode.help = help

  if (element.validation) cleanNode.validation = element.validation
  if (element.options) cleanNode.options = element.options
  if (children.length > 0) cleanNode.children = children

  return cleanNode as FormKitSchemaNode
}

/**
 * Extracts repeater configurations from a form definition.
 */
export function extractRepeaterConfigs(
  formElements: FormElement[],
  locale = 'en',
): RepeaterConfig[] {
  if (!formElements || formElements.length === 0) return []

  const repeaters: RepeaterConfig[] = []

  for (const element of formElements) {
    const formkitType = getFormkitType(element)

    if (formkitType === 'repeater') {
      const childrenSchema = (element.children as FormElement[] || []).flatMap(
        child => transformElementForRepeater(child, locale),
      ) as FormKitSchemaNode[]

      repeaters.push({
        name: element.name as string,
        label: getLocalizedString(element.label, locale),
        addLabel: getLocalizedString(element.addLabel || element.add_label, locale),
        childrenSchema,
        min: element.min as number | undefined,
        max: element.max as number | undefined,
      })
    }
  }

  return repeaters
}

/**
 * Builds a FormKit schema from form elements.
 */
export function buildFormKitSchema(
  formElements: FormElement[],
  options: TransformOptions = {},
): FormKitSchemaNode[] {
  if (!formElements || formElements.length === 0) return []

  try {
    return formElements.flatMap(el => transformElementToSchema(el, options)) as FormKitSchemaNode[]
  }
  catch (error) {
    console.error('Error transforming schema:', error)
    return []
  }
}
