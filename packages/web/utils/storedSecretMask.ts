// The API answers every stored secret with this mask followed by a handle that only resolves for the profile it
// was read from. A mask carried into another profile (clone, import) is therefore refused on save.
export const STORED_SECRET_MASK = '••••••••'

export const isStoredSecret = (value: unknown): value is string =>
  typeof value === 'string' && value.startsWith(STORED_SECRET_MASK)

const clearStoredSecrets = (value: unknown, path: string, clearedPaths: string[]): unknown => {
  if (isStoredSecret(value)) {
    clearedPaths.push(path)
    return ''
  }
  if (Array.isArray(value)) {
    return value.map((item, index) => clearStoredSecrets(item, `${path}.${index}`, clearedPaths))
  }
  if (value && typeof value === 'object') {
    return Object.fromEntries(
      Object.entries(value).map(([key, item]) => [key, clearStoredSecrets(item, path ? `${path}.${key}` : key, clearedPaths)]),
    )
  }
  return value
}

export const withoutStoredSecrets = (
  config: Record<string, unknown>,
): { configuration: Record<string, unknown>, clearedPaths: string[] } => {
  const clearedPaths: string[] = []
  const configuration = clearStoredSecrets(config, '', clearedPaths) as Record<string, unknown>
  return { configuration, clearedPaths }
}
