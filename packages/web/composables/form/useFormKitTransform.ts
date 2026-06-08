import type { FormKitSchemaNode } from '@formkit/core'

export interface RepeaterConfig {
  name: string
  path: string // Full path for nested data access (e.g., "few_shot.few_shot_examples")
  label?: string
  addLabel?: string
  childrenSchema: FormKitSchemaNode[]
  min?: number
  max?: number
}

export interface GroupConfig {
  name: string
  label?: string
  schema: FormKitSchemaNode[]
}

export interface CategorizedElements {
  simpleElements: FormElement[]
  groupElements: FormElement[]
  repeaterElements: FormElement[]
}

export type FormElement = Record<string, unknown>

/**
 * Reads a nested array from an object using a dot-separated path. Pure read: never
 * mutates `obj` (it is called from a render-time `:model-value` getter, where a write
 * into reactive form data would trigger a recursive render loop). Returns an empty array
 * when any path segment is missing or the value is not an array.
 */
export function getNestedValue(
  obj: Record<string, unknown>,
  path: string,
): Record<string, unknown>[] {
  const parts = path.split('.')
  let current: unknown = obj

  for (let i = 0; i < parts.length - 1; i++) {
    if (!current || typeof current !== 'object') return []
    current = (current as Record<string, unknown>)[parts[i]]
  }

  if (!current || typeof current !== 'object') return []
  const value = (current as Record<string, unknown>)[parts.at(-1)!]
  return Array.isArray(value) ? value as Record<string, unknown>[] : []
}

/**
 * Sets a nested array value in an object using a dot-separated path.
 * Creates intermediate objects if they don't exist.
 */
export function setNestedValue(
  obj: Record<string, unknown>,
  path: string,
  value: Record<string, unknown>[],
): void {
  const parts = path.split('.')
  let current: Record<string, unknown> = obj

  for (let i = 0; i < parts.length - 1; i++) {
    const key = parts[i]
    current[key] ??= {}
    current = current[key] as Record<string, unknown>
  }

  current[parts[parts.length - 1]] = value
}

/**
 * Gets the FormKit type from an element, checking both 'formkit' and '$formkit' properties.
 */
export function getFormkitType(element: FormElement): unknown {
  return element.formkit || element.$formkit
}

/**
 * Wraps a FormKit schema node in a fieldset with a legend label.
 * Optionally applies a condition to the fieldset wrapper.
 */
export function wrapInFieldset(
  label: string,
  node: FormKitSchemaNode,
  condition?: string,
  key?: string,
): FormKitSchemaNode[] {
  const fieldset: Record<string, unknown> = {
    $el: 'fieldset',
    attrs: { class: 'formkit-group-fieldset' },
    children: [
      {
        $el: 'legend',
        attrs: { class: 'text-sm font-semibold px-2 text-surface-700 dark:text-surface-300' },
        children: label,
      },
      node,
    ],
  }

  // Apply condition to fieldset wrapper so the entire section hides
  if (condition) {
    fieldset.if = condition
  }

  // Add key to prevent Vue from reusing DOM elements between conditional fieldsets
  if (key) {
    fieldset.key = key
  }

  return [fieldset] as FormKitSchemaNode[]
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
  const groupNode: Record<string, unknown> = {
    $formkit: 'group',
    name: element.name as string,
    children,
    // Keep the group's data in the form context if its `if:` condition (or its
    // wrapping fieldset's) flips false — without preserve, an unmounted group
    // drops every nested value.
    preserve: true,
  }

  // Preserve id for $get() references in conditionals
  if (element.id) groupNode.id = element.id

  // Add key for Vue to prevent DOM reuse between conditional groups
  // This is critical when sibling groups have fields with the same names
  groupNode.key = element.id || element.name

  const condition = element.if as string | undefined
  const key = (element.id || element.name) as string | undefined

  // When wrapped in fieldset, apply condition to fieldset (outer wrapper)
  // Otherwise apply to the group itself
  if (label) {
    return wrapInFieldset(label, groupNode as FormKitSchemaNode, condition, key)
  }

  if (condition) groupNode.if = condition
  return groupNode as FormKitSchemaNode
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

function buildLocaleInputProperties(
  element: FormElement,
  label: string | undefined,
  locale: string,
): Record<string, unknown> {
  // `preserve: true` keeps the input's value in the form context when an `if:`
  // condition (nullable toggle or backend-supplied `condition_if`) unmounts it.
  const cleanNode: Record<string, unknown> = { $formkit: 'localeInput', preserve: true }

  if (element.name) cleanNode.name = element.name
  if (label) cleanNode.label = label

  // Preserve id for $get() references in conditionals
  if (element.id) cleanNode.id = element.id

  // Stable key prevents Vue from reusing this DOM node across sibling schema entries
  // (critical when conditional `if:` siblings mount/unmount around it). `element.id`
  // is auto-assigned per FormkitElement and `element.name` is FormKit-unique within
  // a group by construction, so collisions cannot occur via this fallback chain.
  cleanNode.key = (element.id as string | undefined) ?? (element.name as string)

  // Preserve conditional visibility (FormKit uses 'if' for schema conditionals)
  if (element.if) cleanNode.if = element.if

  const help = getLocalizedString(element.help, locale)
  if (help) cleanNode.help = help

  // For localeInput, pass placeholder as full LocaleString object (not localized)
  if (element.placeholder) cleanNode.placeholder = element.placeholder

  // Pass inputType and rows props (support both camelCase and snake_case for backwards compatibility)
  const inputType = element.inputType || element.input_type
  if (inputType) cleanNode.inputType = inputType
  if (element.rows !== undefined) cleanNode.rows = element.rows

  if (element.validation) cleanNode.validation = element.validation

  return cleanNode
}

// Fields that should be excluded from passthrough (internal markers, already handled, or need transformation)
const EXCLUDED_FIELDS = new Set([
  'is_formkit_element', // Internal marker
  'formkit', // Handled separately as $formkit
  '$formkit', // Handled separately
  'label', // Transformed via getLocalizedString
  'help', // Transformed via getLocalizedString
  'placeholder', // Transformed via getLocalizedString
  'children', // Handled separately for recursion
  'nullable', // Wrapper-level signal for the transform; never a FormKit/PrimeVue prop
  // Backend serialises the Pydantic default into element.value (form duality). FormKit pushes
  // schema `value` up to the parent v-model on input registration, which would clobber the
  // loaded data with the backend default. Defaults belong in data, seeded via seedFormDefaults.
  'value',
])

function buildNodeProperties(
  element: FormElement,
  formkitType: unknown,
  label: string | undefined,
  locale: string,
  optionsResolver?: (element: FormElement) => unknown[] | undefined,
): Record<string, unknown> {
  // Handle localeInput specially
  if (formkitType === 'localeInput') {
    return buildLocaleInputProperties(element, label, locale)
  }

  // `preserve: true` keeps the input's value in the form context when an `if:`
  // condition (nullable toggle or backend-supplied `condition_if`) unmounts it.
  const cleanNode: Record<string, unknown> = { $formkit: formkitType, preserve: true }

  // Pass through all properties except excluded ones
  for (const [key, value] of Object.entries(element)) {
    if (EXCLUDED_FIELDS.has(key)) continue
    if (value === undefined || value === null) continue
    cleanNode[key] = value
  }

  // Apply transformations for localized fields
  if (label) cleanNode.label = label

  const help = getLocalizedString(element.help, locale)
  if (help) cleanNode.help = help

  const placeholder = getLocalizedString(element.placeholder, locale)
  if (placeholder) cleanNode.placeholder = placeholder

  // Resolve options if resolver provided
  const options = resolveElementOptions(element, optionsResolver)
  if (options) cleanNode.options = options

  // Stable key prevents Vue from reusing this DOM node across sibling schema entries
  // (critical when conditional `if:` siblings mount/unmount around it). `element.id`
  // is auto-assigned per FormkitElement and `element.name` is FormKit-unique within
  // a group by construction, so collisions cannot occur via this fallback chain.
  cleanNode.key = (element.id as string | undefined) ?? (element.name as string)

  return cleanNode
}

/**
 * Builds the toggle name used to gate a nullable form element.
 */
export function nullableToggleName(fieldName: string): string {
  return `__${fieldName}__enabled`
}

/**
 * Builds a unique FormKit input id for the synthetic toggle that gates a nullable element.
 * Uses the element's existing id (backend ref) when available so the id is unique across
 * the whole form schema; falls back to the field name. Dots are replaced because FormKit
 * `$get()` lookups expect slug-style ids.
 */
function nullableToggleId(element: FormElement): string {
  const base = (element.id as string | undefined) ?? (element.name as string)
  return `${base.replace(/\./g, '__')}__enabled_toggle`
}

/**
 * Combines a synthetic toggle condition with any existing condition_if.
 */
function combineConditions(toggleCondition: string, existing: string | undefined): string {
  if (!existing) return toggleCondition
  if (existing.startsWith('$:')) {
    return `$: ${toggleCondition.slice(1)} && (${existing.slice(2).trim()})`
  }
  return `$: ${toggleCondition.slice(1)} && (${existing.slice(1)})`
}

function buildNullableToggleNode(element: FormElement, label: string | undefined): Record<string, unknown> {
  const fieldName = element.name as string
  const toggleId = nullableToggleId(element)
  return {
    $formkit: 'primeCheckbox',
    name: nullableToggleName(fieldName),
    id: toggleId,
    key: toggleId,
    label: label ? `Enable ${label}` : 'Enable',
    binary: true,
  }
}

function applyNullableToggle(
  element: FormElement,
  baseNode: FormKitSchemaNode | FormKitSchemaNode[],
  label: string | undefined,
): FormKitSchemaNode[] {
  const nodeArray = Array.isArray(baseNode) ? baseNode : [baseNode]
  return [buildNullableToggleNode(element, label) as FormKitSchemaNode, ...nodeArray]
}

function gateElement(element: FormElement, toggleCondition: string): FormElement {
  return { ...element, if: combineConditions(toggleCondition, element.if as string | undefined) }
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

  const isNullable = element.nullable === true
  const toggleCondition = isNullable ? `$get(${nullableToggleId(element)}).value` : undefined

  if (formkitType === 'group') {
    const gatedElement = isNullable ? gateElement(element, toggleCondition!) : element
    const groupNode = createGroupNode(gatedElement, children, label)
    return isNullable ? applyNullableToggle(element, groupNode, label) : groupNode
  }

  const cleanNode = buildNodeProperties(element, formkitType, label, locale, optionsResolver)
  if (children.length > 0) cleanNode.children = children
  if (isNullable) {
    cleanNode.if = combineConditions(toggleCondition!, element.if as string | undefined)
    return applyNullableToggle(element, cleanNode as FormKitSchemaNode, label)
  }

  return cleanNode as FormKitSchemaNode
}

function buildLeafNodeForRepeater(
  element: FormElement,
  formkitType: unknown,
  label: string | undefined,
  locale: string,
  children: FormKitSchemaNode[],
): Record<string, unknown> {
  if (formkitType === 'localeInput') {
    return buildLocaleInputProperties(element, label, locale)
  }

  const cleanNode: Record<string, unknown> = { $formkit: formkitType, preserve: true }
  for (const [key, value] of Object.entries(element)) {
    if (EXCLUDED_FIELDS.has(key)) continue
    if (value === undefined || value === null) continue
    cleanNode[key] = value
  }
  if (label) cleanNode.label = label
  const help = getLocalizedString(element.help, locale)
  if (help) cleanNode.help = help
  if (children.length > 0) cleanNode.children = children
  cleanNode.key = (element.id as string | undefined) ?? (element.name as string)
  return cleanNode
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
  const isNullable = element.nullable === true
  const toggleCondition = isNullable ? `$get(${nullableToggleId(element)}).value` : undefined

  if (formkitType === 'group') {
    const gatedElement = isNullable ? gateElement(element, toggleCondition!) : element
    const groupNode = createGroupNode(gatedElement, children, label)
    return isNullable ? applyNullableToggle(element, groupNode, label) : groupNode
  }

  const cleanNode = buildLeafNodeForRepeater(element, formkitType, label, locale, children)
  if (isNullable) {
    cleanNode.if = combineConditions(toggleCondition!, element.if as string | undefined)
    return applyNullableToggle(element, cleanNode as FormKitSchemaNode, label)
  }

  return cleanNode as FormKitSchemaNode
}

/**
 * Extracts repeater configurations from a form definition.
 */
export function extractRepeaterConfigs(
  formElements: FormElement[],
  locale = 'en',
  parentPath = '',
): RepeaterConfig[] {
  if (!formElements || formElements.length === 0) return []

  const repeaters: RepeaterConfig[] = []

  for (const element of formElements) {
    const formkitType = getFormkitType(element)
    const elementName = element.name as string

    if (formkitType === 'repeater') {
      const childrenSchema = (element.children as FormElement[] || []).flatMap(
        child => transformElementForRepeater(child, locale),
      ) as FormKitSchemaNode[]

      // Build full path for nested data access
      const fullPath = parentPath ? `${parentPath}.${elementName}` : elementName

      repeaters.push({
        name: elementName,
        path: fullPath,
        label: getLocalizedString(element.label, locale),
        addLabel: getLocalizedString(element.addLabel || element.add_label, locale),
        childrenSchema,
        min: element.min as number | undefined,
        max: element.max as number | undefined,
      })
    }
    else if (formkitType === 'group' && element.children) {
      // Recursively search for repeaters inside groups, passing the current path
      const groupPath = parentPath ? `${parentPath}.${elementName}` : elementName
      const nestedRepeaters = extractRepeaterConfigs(
        element.children as FormElement[],
        locale,
        groupPath,
      )
      repeaters.push(...nestedRepeaters)
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

const LOCALE_KEYS = new Set(['de', 'en', 'fr', 'it'])

/**
 * Checks if a value is a LocaleString object (has only locale keys: de, en, fr, it).
 */
function isLocaleStringObject(value: unknown): value is Record<string, unknown> {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    return false
  }
  const keys = Object.keys(value as object)
  return keys.length > 0 && keys.every(key => LOCALE_KEYS.has(key))
}

/**
 * Normalizes a LocaleString object:
 * - Always returns an object with all locale fields as strings (empty string for unfilled)
 * - Never returns null - backend expects a dict/LocaleString object, not null
 *
 * Backend validation will determine if empty values are acceptable based on field constraints.
 */
function normalizeLocaleString(localeObj: Record<string, unknown>): Record<string, string> {
  return {
    de: (localeObj.de as string) || '',
    en: (localeObj.en as string) || '',
    fr: (localeObj.fr as string) || '',
    it: (localeObj.it as string) || '',
  }
}

/**
 * Recursively normalizes LocaleString fields in form data before submission.
 * - LocaleString objects → all fields normalized to strings (empty string for unfilled)
 * - Other values are recursively processed
 */
export function normalizeFormLocaleStrings<T>(data: T): T {
  if (data === null || data === undefined) {
    return data
  }

  if (Array.isArray(data)) {
    return data.map(item => normalizeFormLocaleStrings(item)) as T
  }

  if (typeof data === 'object') {
    if (isLocaleStringObject(data)) {
      return normalizeLocaleString(data as Record<string, unknown>) as T
    }

    const result: Record<string, unknown> = {}
    for (const [key, value] of Object.entries(data)) {
      result[key] = normalizeFormLocaleStrings(value)
    }
    return result as T
  }

  return data
}

/**
 * Walks the form schema; for every nullable element whose synthetic toggle is off,
 * replaces the actual field value with `null`. Always strips synthetic toggle keys.
 */
export function coerceNullableToggles(
  data: Record<string, unknown>,
  elements: FormElement[],
): Record<string, unknown> {
  const result: Record<string, unknown> = { ...data }

  for (const element of elements) {
    const name = element.name as string
    if (element.nullable === true) {
      const toggleKey = nullableToggleName(name)
      const enabled = result[toggleKey] === true
      Reflect.deleteProperty(result, toggleKey)
      if (!enabled) {
        result[name] = null
        continue
      }
    }

    const formkitType = getFormkitType(element)
    const children = (element.children as FormElement[] | undefined) ?? []
    const value = result[name]

    if (formkitType === 'group' && value && typeof value === 'object' && !Array.isArray(value)) {
      result[name] = coerceNullableToggles(value as Record<string, unknown>, children)
    }
    else if (formkitType === 'repeater' && Array.isArray(value)) {
      result[name] = value.map(item =>
        item && typeof item === 'object' && !Array.isArray(item)
          ? coerceNullableToggles(item as Record<string, unknown>, children)
          : item,
      )
    }
  }

  for (const key of Object.keys(result)) {
    if (key.startsWith('__') && key.endsWith('__enabled')) {
      Reflect.deleteProperty(result, key)
    }
  }

  return result
}

/**
 * Recursively fills missing leaf keys with the backend's serialised Pydantic defaults
 * (`element.value`). FormKit no longer receives `value` in the schema (it would clobber
 * the v-model on registration), so defaults must be merged into the form data instead.
 * Existing values — including falsy ones like `false` or `""` — are preserved.
 *
 * NOTE: This helper is load-bearing for edit/clone/template flows but has no direct
 * unit tests yet — Vitest is not configured for packages/web (see packages/web/CLAUDE.md).
 * The Python-side `Form.to_formkit_form()` tests in packages/core lock in what
 * `element.value` looks like; behaviour here is exercised end-to-end on agent and
 * process edit forms.
 */
/**
 * Seed a group field's value: leave a disabled nullable group as `null`; otherwise
 * materialise its children's defaults (starting from the existing object when present).
 * `coerceNullableToggles` re-nullifies disabled subtrees at submit time, so seeding a
 * group whose toggle will end up off is safe.
 */
function seedGroupDefault(value: unknown, children: FormElement[]): Record<string, unknown> | null {
  if (value === null) return null
  const groupValue = value && typeof value === 'object' && !Array.isArray(value)
    ? value as Record<string, unknown>
    : {}
  return seedFormDefaults(groupValue, children)
}

/**
 * Seed a repeater field's value: recurse into each existing item, or materialise an
 * empty array for an untouched repeater (done here at load time rather than lazily in
 * the render-time `:model-value` getter, which must stay pure). Any other value is
 * returned unchanged.
 */
function seedRepeaterDefault(value: unknown, children: FormElement[]): unknown {
  if (Array.isArray(value)) {
    return value.map(item =>
      item && typeof item === 'object' && !Array.isArray(item)
        ? seedFormDefaults(item as Record<string, unknown>, children)
        : item,
    )
  }
  return value === undefined ? [] : value
}

export function seedFormDefaults(
  data: Record<string, unknown>,
  elements: FormElement[],
): Record<string, unknown> {
  const result: Record<string, unknown> = { ...data }

  for (const element of elements) {
    const name = element.name as string
    const formkitType = getFormkitType(element)
    const children = (element.children as FormElement[] | undefined) ?? []
    const value = result[name]

    if (formkitType === 'group') {
      result[name] = seedGroupDefault(value, children)
    }
    else if (formkitType === 'repeater') {
      result[name] = seedRepeaterDefault(value, children)
    }
    else if (!(name in result) && element.value !== undefined) {
      result[name] = element.value
    }
  }

  return result
}

/**
 * Recursively seeds synthetic toggle values from initial data: toggle is on iff the
 * matching field was non-null/undefined in the source data.
 */
export function seedNullableToggles(
  data: Record<string, unknown>,
  elements: FormElement[],
): Record<string, unknown> {
  const result: Record<string, unknown> = { ...data }

  for (const element of elements) {
    const name = element.name as string
    if (element.nullable === true) {
      result[nullableToggleName(name)] = result[name] !== null && result[name] !== undefined
    }

    const formkitType = getFormkitType(element)
    const children = (element.children as FormElement[] | undefined) ?? []
    const value = result[name]

    if (formkitType === 'group' && value && typeof value === 'object' && !Array.isArray(value)) {
      result[name] = seedNullableToggles(value as Record<string, unknown>, children)
    }
    else if (formkitType === 'repeater' && Array.isArray(value)) {
      result[name] = value.map(item =>
        item && typeof item === 'object' && !Array.isArray(item)
          ? seedNullableToggles(item as Record<string, unknown>, children)
          : item,
      )
    }
  }

  return result
}

/**
 * Categorizes form elements into simple inputs, groups, and repeaters.
 * Used for organizing form elements into stepper steps.
 */
export function categorizeFormElements(formElements: FormElement[]): CategorizedElements {
  if (!formElements || formElements.length === 0) {
    return { simpleElements: [], groupElements: [], repeaterElements: [] }
  }

  const simpleElements: FormElement[] = []
  const groupElements: FormElement[] = []
  const repeaterElements: FormElement[] = []

  for (const element of formElements) {
    const formkitType = getFormkitType(element)

    if (formkitType === 'group') {
      groupElements.push(element)
    }
    else if (formkitType === 'repeater') {
      repeaterElements.push(element)
    }
    else {
      simpleElements.push(element)
    }
  }

  return { simpleElements, groupElements, repeaterElements }
}

/**
 * Extracts group configurations from form elements.
 * Similar to extractRepeaterConfigs but for group elements.
 */
export function extractGroupConfigs(
  formElements: FormElement[],
  locale = 'en',
): GroupConfig[] {
  if (!formElements || formElements.length === 0) return []

  const groups: GroupConfig[] = []

  for (const element of formElements) {
    const formkitType = getFormkitType(element)

    if (formkitType === 'group') {
      const schema = transformElementToSchema(element, { locale })
      const schemaArray = Array.isArray(schema) ? schema : [schema]

      groups.push({
        name: element.name as string,
        label: getLocalizedString(element.label, locale),
        schema: schemaArray,
      })
    }
  }

  return groups
}
