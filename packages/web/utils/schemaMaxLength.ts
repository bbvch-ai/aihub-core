interface JsonSchemaProperty {
  maxLength?: number
  anyOf?: readonly JsonSchemaProperty[]
}

// Forms read a text field's limit from the generated SDK schema rather than restating the
// number the API DTO declares, so the two cannot drift apart. A nullable field nests its
// `maxLength` inside `anyOf`.
export const schemaMaxLength = (schema: { properties: object }, field: string): number | undefined => {
  const property = (schema.properties as Record<string, JsonSchemaProperty | undefined>)[field]
  return property?.maxLength ?? property?.anyOf?.find(option => option.maxLength !== undefined)?.maxLength
}
