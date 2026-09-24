<template>
  <div class="flex flex-col gap-1">
    <MultiSelect
      v-model="selectedKeys"
      :input-id="inputId"
      :options="groupedOptions"
      option-group-label="label"
      option-group-children="items"
      option-label="displayName"
      option-value="key"
      :placeholder="placeholder ?? t('lib.knowledgeCollections.placeholder')"
      :filter="filter"
      :loading="isLoading"
      :disabled="!hasAgent"
      display="chip"
      class="w-full"
    >
      <template #optiongroup="{ option }">
        <div class="flex items-center gap-2">
          <Icon
            name="mage:database"
            size="1.2em"
          />
          <span>{{ option.label }}</span>
        </div>
      </template>
      <template #option="{ option }">
        <div class="flex items-center gap-2">
          <Icon
            name="mage:folder"
            size="1.2em"
          />
          <span>{{ option.displayName }}</span>
        </div>
      </template>
    </MultiSelect>
    <small class="text-surface-500">
      {{ hint }}
    </small>
  </div>
</template>

<script setup lang="ts">
import { getAgentInstance, getDatabases } from '@core/sdk/client'

import type { DatabaseDto } from '@core/sdk/client'
import type { FormKitNode } from '@formkit/core'

/**
 * A collection is only addressable as a (database, collection) pair — the same name may exist in more
 * than one database — so the form value is a list of pairs, the shape `RAGStartEvent.selected_namespaces`
 * takes. PrimeVue selects on a primitive, hence the `database/collection` key used inside this component.
 */
interface BucketNamespacePair {
  bucket_name: string
  namespace_name: string
}

interface AgentRefValue {
  agent_class?: string | null
  agent_id?: string | null
}

/** One retriever's vector store, as it is saved in the referenced agent's configuration. */
interface VectorStoreConfig {
  collection_name?: string
  index_namespaces?: string[]
  all_namespaces?: boolean
}

interface CollectionOption {
  key: string
  displayName: string
  pair: BucketNamespacePair
}

interface CollectionGroup {
  label: string
  items: CollectionOption[]
}

interface KnowledgeCollectionSelectorProps {
  context: {
    node: {
      input: (value: BucketNamespacePair[] | null) => void
      at: (address: string) => FormKitNode | null | undefined
    }
    value?: BucketNamespacePair[] | null
    attrs: Record<string, unknown>
    id?: string
    agentRef?: string
    placeholder?: string
    filter?: boolean
  }
}

const props = defineProps<KnowledgeCollectionSelectorProps>()
const { t } = useI18n()
const { tenantId } = useTenant()

const agentRefPath = computed(() => props.context.agentRef)
const placeholder = computed(() => props.context.placeholder)
const filter = computed(() => props.context.filter ?? true)
const inputId = computed(() => `${props.context.id ?? 'knowledge-collections'}-select`)

const agentRef = ref<AgentRefValue | null>(null)
const collections = ref<BucketNamespacePair[]>([])
const databaseNames = ref<Record<string, string>>({})
const collectionNames = ref<Record<string, string>>({})
const isLoading = ref(false)

const hasAgent = computed(() => !!agentRef.value?.agent_class && !!agentRef.value?.agent_id)

const currentValue = computed<BucketNamespacePair[]>(() => props.context.value ?? [])

function keyOf(pair: BucketNamespacePair): string {
  return `${pair.bucket_name}/${pair.namespace_name}`
}

function collectionLabel(pair: BucketNamespacePair): string {
  return collectionNames.value[keyOf(pair)] || pair.namespace_name
}

const groupedOptions = computed<CollectionGroup[]>(() => {
  const byDatabase = new Map<string, CollectionOption[]>()
  for (const pair of collections.value) {
    const options = byDatabase.get(pair.bucket_name) ?? []
    options.push({
      key: keyOf(pair),
      displayName: collectionLabel(pair),
      pair,
    })
    byDatabase.set(pair.bucket_name, options)
  }
  const groups = [...byDatabase.entries()].map(([database, items]) => ({
    label: databaseNames.value[database] || database,
    items,
  }))

  // PrimeVue labels a chip from the matching option, so a selection the agent does not retrieve from
  // would otherwise render as its remove icon and nothing else. It is listed under its own group,
  // qualified by database because that is usually what went wrong — the selection was made against a
  // different agent — and so the narrowing the run still applies stays visible enough to act on.
  const available = new Set(collections.value.map(keyOf))
  const unavailable = currentValue.value.filter(pair => !available.has(keyOf(pair)))
  if (unavailable.length === 0) return groups

  return [...groups, {
    label: t('lib.knowledgeCollections.unavailable'),
    items: unavailable.map(pair => ({
      key: keyOf(pair),
      displayName: `${databaseNames.value[pair.bucket_name] || pair.bucket_name} / ${collectionLabel(pair)}`,
      pair,
    })),
  }]
})

// A selection saved before the referenced agent lost a collection would silently disappear from the
// chips on load, so it stays listed until the user changes the selection themselves.
const selectedKeys = computed({
  get: () => currentValue.value.map(keyOf),
  set: (keys: string[]) => {
    const byKey = new Map(collections.value.map(pair => [keyOf(pair), pair]))
    props.context.node.input(keys.map(key => byKey.get(key) ?? currentValue.value.find(pair => keyOf(pair) === key))
      .filter((pair): pair is BucketNamespacePair => !!pair))
  },
})

const hint = computed(() => {
  if (!agentRefPath.value) return t('lib.knowledgeCollections.noSource')
  if (!hasAgent.value) return t('lib.knowledgeCollections.noAgent')
  if (!isLoading.value && collections.value.length === 0) return t('lib.knowledgeCollections.empty')
  return t('lib.knowledgeCollections.help')
})

/**
 * The collections the referenced agent actually retrieves from: the namespaces each of its retrievers
 * names, or — for a retriever scoped to a whole database — every namespace that database holds. Anything
 * outside this set would be dropped at runtime and the reply answered from nothing, which is why the
 * catalogue alone is not offered here.
 */
function collectionsFromRetrievers(configuration: Record<string, unknown>, databases: DatabaseDto[]): BucketNamespacePair[] {
  const retrievers = Array.isArray(configuration.retrievers) ? configuration.retrievers : []
  const pairs: BucketNamespacePair[] = []
  const seen = new Set<string>()

  for (const retriever of retrievers) {
    const store = (retriever as Record<string, unknown>)?.vector_store as VectorStoreConfig | undefined
    const database = store?.collection_name
    if (!database) continue

    const namespaces = store?.all_namespaces
      ? (databases.find(entry => entry.name === database)?.namespaces ?? []).map(namespace => namespace.name)
      : (store?.index_namespaces ?? [])

    for (const namespace of namespaces) {
      const pair = { bucket_name: database, namespace_name: namespace }
      const key = keyOf(pair)
      if (seen.has(key)) continue
      seen.add(key)
      pairs.push(pair)
    }
  }
  return pairs
}

async function loadCollections() {
  const agentClass = agentRef.value?.agent_class
  const agentId = agentRef.value?.agent_id
  if (!agentClass || !agentId) {
    collections.value = []
    return
  }

  isLoading.value = true
  try {
    const [instance, databases] = await Promise.all([
      getAgentInstance({
        composable: '$fetch',
        path: { tenant_id: tenantId.value!, agent_class: agentClass, agent_id: agentId },
      }),
      getDatabases({ composable: '$fetch', path: { tenant_id: tenantId.value! } }),
    ])
    databaseNames.value = Object.fromEntries(
      databases.map(database => [database.name, database.display_name || database.name]),
    )
    collectionNames.value = Object.fromEntries(
      databases.flatMap(database => database.namespaces
        .filter(namespace => namespace.display_name)
        .map(namespace => [keyOf({ bucket_name: database.name, namespace_name: namespace.name }), namespace.display_name!])),
    )
    collections.value = collectionsFromRetrievers(instance.configuration ?? {}, databases)
  }
  catch (error) {
    console.error(`Failed to load knowledge collections for "${agentClass}/${agentId}":`, error)
    collections.value = []
  }
  finally {
    isLoading.value = false
  }
}

/**
 * The path arrives relative to the form root and is anchored here, never on the backend: FormKit compiles any
 * schema string beginning with `$` as an expression, so a path shipped as `$root.…` is evaluated against the form
 * data and reaches this component as `undefined`.
 */
function readAgentRef(): AgentRefValue | null {
  if (!agentRefPath.value) return null
  return (props.context.node.at(`$root.${agentRefPath.value}`)?.value as AgentRefValue | undefined) ?? null
}

function syncAgentRef() {
  const next = readAgentRef()
  if (next?.agent_class === agentRef.value?.agent_class && next?.agent_id === agentRef.value?.agent_id) return
  agentRef.value = next
  loadCollections()
}

// The agent lives elsewhere on the form — a sibling group here, a different step in other layouts — so the
// only dependable signal that it changed is the root form committing. Values on FormKit nodes are not Vue
// reactive, and re-reading on every commit is cheap because `syncAgentRef` compares before refetching.
let rootNode: FormKitNode | null | undefined
let receipt: string | undefined
onMounted(() => {
  syncAgentRef()
  rootNode = props.context.node.at('$root')
  receipt = rootNode?.on('commit', syncAgentRef)
})

onUnmounted(() => {
  if (receipt) rootNode?.off(receipt)
})
</script>
