<template>
  <div class="flex flex-col gap-4">
    <!-- Database Selection -->
    <div>
      <label class="mb-1 block text-sm font-medium">
        {{ t('lib.vectorStore.database.label') }}
      </label>
      <Select
        v-model="selectedDatabase"
        :options="databaseOptions"
        option-label="displayName"
        option-value="name"
        :placeholder="databasePlaceholder ?? t('common.selectDatabase')"
        :filter="filter"
        :loading="isLoading"
        class="w-full"
      >
        <template #option="{ option }">
          <div class="flex items-center gap-2">
            <Icon
              name="mage:database"
              size="1.2em"
            />
            <span>{{ option.displayName }}</span>
          </div>
        </template>
        <template #value="{ value }">
          <div
            v-if="value"
            class="flex items-center gap-2"
          >
            <Icon
              name="mage:database"
              size="1.2em"
            />
            <span>{{ getDatabaseDisplayName(value) }}</span>
          </div>
        </template>
      </Select>
    </div>

    <!-- Namespace Selection (shown when database selected) -->
    <div v-if="selectedDatabase">
      <label class="mb-1 block text-sm font-medium">
        {{ t('lib.vectorStore.namespaces.label') }}
      </label>
      <MultiSelect
        v-model="selectedNamespaces"
        :options="namespaceOptions"
        option-label="displayName"
        option-value="name"
        :placeholder="namespacePlaceholder ?? t('lib.vectorStore.namespaces.placeholder')"
        :filter="filter"
        display="chip"
        class="w-full"
      >
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
      <small class="mt-1 text-surface-500">
        {{ t('lib.vectorStore.namespaces.help') }}
      </small>
    </div>
  </div>
</template>

<script setup lang="ts">
import { getDatabases } from '@core/sdk/client'
import { useChangeCase } from '@vueuse/integrations/useChangeCase'

import type { DatabaseDto } from '@core/sdk/client'

interface VectorStoreInputValue {
  collection_name: string
  index_namespaces: string[]
}

interface DatabaseOption {
  name: string
  displayName: string
}

interface NamespaceOption {
  name: string
  displayName: string
}

interface VectorStoreInputProps {
  context: {
    node: {
      input: (value: VectorStoreInputValue | null) => void
    }
    value?: VectorStoreInputValue | null
    attrs: Record<string, unknown>
    databasePlaceholder?: string
    namespacePlaceholder?: string
    filter?: boolean
  }
}

const props = defineProps<VectorStoreInputProps>()
const { t } = useI18n()
const { tenantId } = useTenant()

// Get custom props from context (FormKit passes them there, not as direct props)
const databasePlaceholder = computed(() => props.context.databasePlaceholder)
const namespacePlaceholder = computed(() => props.context.namespacePlaceholder)
const filter = computed(() => props.context.filter ?? true)

// State
const databases = ref<DatabaseDto[]>([])
const isLoading = ref(false)

// Get current value from context
const currentValue = computed(() => props.context.value ?? null)

// Selected database (computed property that syncs with the form value)
const selectedDatabase = computed({
  get: () => currentValue.value?.collection_name ?? null,
  set: (value: string | null) => {
    if (value) {
      // When database changes, reset namespaces
      emitValue(value, [])
    }
    else {
      props.context.node.input(null)
    }
  },
})

// Selected namespaces (computed property that syncs with the form value)
const selectedNamespaces = computed({
  get: () => currentValue.value?.index_namespaces ?? [],
  set: (value: string[]) => {
    if (selectedDatabase.value) {
      emitValue(selectedDatabase.value, value)
    }
  },
})

// Emit complete value object
function emitValue(collectionName: string, namespaces: string[]) {
  props.context.node.input({
    collection_name: collectionName,
    index_namespaces: namespaces,
  })
}

// Database options for select
const databaseOptions = computed<DatabaseOption[]>(() =>
  databases.value.map(db => ({
    name: db.name,
    displayName: db.display_name || useChangeCase(db.name, 'capitalCase'),
  })),
)

// Namespace options based on selected database
const namespaceOptions = computed<NamespaceOption[]>(() => {
  if (!selectedDatabase.value)
    return []
  const db = databases.value.find(d => d.name === selectedDatabase.value)
  if (!db)
    return []
  return db.namespaces.map(ns => ({
    name: ns.name,
    displayName: ns.display_name || useChangeCase(ns.name, 'capitalCase'),
  }))
})

function getDatabaseDisplayName(name: string): string {
  const option = databaseOptions.value.find(opt => opt.name === name)
  return option?.displayName ?? name
}

async function fetchDatabases() {
  isLoading.value = true
  try {
    const response = await getDatabases({
      composable: '$fetch',
      path: { tenant_id: tenantId.value! },
    })
    databases.value = response
  }
  catch (error) {
    console.error('Failed to fetch databases:', error)
    databases.value = []
  }
  finally {
    isLoading.value = false
  }
}

// Fetch databases on mount
onMounted(() => {
  fetchDatabases()
})
</script>
