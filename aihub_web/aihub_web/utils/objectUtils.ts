/**
 * Utility functions for transforming between nested objects and flat dot-notation objects.
 * Used for FormKit compatibility where form field names use dot-notation (e.g., "llm.model_name")
 * but the API stores data as nested objects (e.g., { llm: { model_name: "..." } }).
 */

type NestedObject = Record<string, unknown>
type FlatObject = Record<string, unknown>

// TODO check if this is necessary
/**
 * Flattens a nested object into a flat object with dot-notation keys.
 *
 * @example
 * flattenObject({ llm: { model_name: "gpt-4", params: { temp: 0.7 } } })
 * // Returns: { "llm.model_name": "gpt-4", "llm.params.temp": 0.7 }
 */
export function flattenObject(obj: NestedObject, prefix = ''): FlatObject {
  const result: FlatObject = {}

  for (const [key, value] of Object.entries(obj)) {
    const newKey = prefix ? `${prefix}.${key}` : key

    if (value !== null && typeof value === 'object' && !Array.isArray(value)) {
      // Recursively flatten nested objects
      Object.assign(result, flattenObject(value as NestedObject, newKey))
    } else {
      // Leaf value (primitive, array, or null)
      result[newKey] = value
    }
  }

  return result
}

/**
 * Unflattens a flat object with dot-notation keys into a nested object.
 *
 * @example
 * unflattenObject({ "llm.model_name": "gpt-4", "llm.params.temp": 0.7 })
 * // Returns: { llm: { model_name: "gpt-4", params: { temp: 0.7 } } }
 */
export function unflattenObject(obj: FlatObject): NestedObject {
  const result: NestedObject = {}

  for (const [key, value] of Object.entries(obj)) {
    const keys = key.split('.')
    let current = result

    for (let i = 0; i < keys.length - 1; i++) {
      const k = keys[i]
      if (!(k in current) || typeof current[k] !== 'object' || current[k] === null) {
        current[k] = {}
      }
      current = current[k] as NestedObject
    }

    current[keys[keys.length - 1]] = value
  }

  return result
}

/**
 * Deep merges override object into base object.
 * Override values take precedence; nested objects are merged recursively.
 *
 * @example
 * deepMerge({ a: { b: 1, c: 2 } }, { a: { b: 3 } })
 * // Returns: { a: { b: 3, c: 2 } }
 */
export function deepMerge(base: NestedObject, override: NestedObject): NestedObject {
  const result = {...base}

  for (const [key, value] of Object.entries(override)) {
    if (
      key in result
      && result[key] !== null
      && typeof result[key] === 'object'
      && !Array.isArray(result[key])
      && value !== null
      && typeof value === 'object'
      && !Array.isArray(value)
    ) {
      result[key] = deepMerge(result[key] as NestedObject, value as NestedObject)
    } else {
      result[key] = value
    }
  }

  return result
}
