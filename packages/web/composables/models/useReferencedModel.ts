import type { ModelInfoDto } from '@core/sdk/client'
import type { FormKitNode } from '@formkit/core'

/**
 * The model picked by another field of the same form, for inputs whose bounds or availability depend on it.
 *
 * The path arrives relative to the form root (the backend resolves it) and is anchored here: FormKit compiles any
 * schema string beginning with `$` as an expression. Values on FormKit nodes are not Vue reactive, so the root's
 * `commit` is the signal that the picker changed, as in `KnowledgeCollectionSelector`.
 */
export const useReferencedModel = (node: FormKitNode, modelRefPath: () => string | undefined) => {
  const { modelTypes } = useModelsList()
  const modelName = ref<string | null>(null)

  function syncModelName() {
    const path = modelRefPath()
    const next = path ? (node.at(`$root.${path}`)?.value as string | null | undefined) ?? null : null
    if (next !== modelName.value) modelName.value = next
  }

  const modelInfo = computed<ModelInfoDto | null>(() => {
    if (!modelName.value) return null
    const model = (modelTypes.value ?? []).flatMap(group => group.models).find(entry => entry.model_name === modelName.value)
    return model?.model_info ?? null
  })

  let rootNode: FormKitNode | null | undefined
  let receipt: string | undefined
  onMounted(() => {
    syncModelName()
    rootNode = node.at('$root')
    receipt = rootNode?.on('commit', syncModelName)
  })
  onUnmounted(() => {
    if (receipt) rootNode?.off(receipt)
  })

  return { modelName, modelInfo }
}
