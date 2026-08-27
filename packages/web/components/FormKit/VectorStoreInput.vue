<template>
  <div class="flex flex-col gap-4">
    <!-- Database Selection -->
    <div>
      <label
        for="vector-store-database-select"
        class="mb-1 block text-sm font-medium"
      >
        {{ t('lib.vectorStore.database.label') }}
      </label>
      <Select
        v-model="selectedDatabase"
        :aria-label="t('lib.vectorStore.database.label')"
        input-id="vector-store-database-select"
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
      <label
        for="vector-store-namespaces-select"
        class="mb-1 block text-sm font-medium"
      >
        {{ t('lib.vectorStore.namespaces.label') }}
      </label>
      <MultiSelect
        v-model="selectedNamespaces"
        input-id="vector-store-namespaces-select"
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

    <!-- Allowed metadata filter fields (shown when database selected) -->
    <div v-if="selectedDatabase">
      <label
        for="vector-store-filter-fields-input"
        class="mb-1 block text-sm font-medium"
      >
        {{ t('lib.vectorStore.allowedFilterFields.label') }}
      </label>
      <ChipsInput :context="chipsInputContext" />
      <small class="mt-1 text-surface-500">
        {{ t('lib.vectorStore.allowedFilterFields.help') }}
      </small>
    </div>
  </div>
</template>

<script setup lang="ts">
import ChipsInput from '@core/components/FormKit/ChipsInput.vue'
import { capitalCase } from 'change-case'

import type { DatabaseDto } from '@core/sdk/client'

interface VectorStoreInputValue {
  collection_name: string
  index_namespaces: string[]
  allowed_metadata_filter_fields: string[]
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
    allowedFilterFieldsPlaceholder?: string
    filter?: boolean
  }
}

const props = defineProps<VectorStoreInputProps>()
const { t } = useI18n()

// Get custom props from context (FormKit passes them there, not as direct props)
const databasePlaceholder = computed(() => props.context.databasePlaceholder)
const namespacePlaceholder = computed(() => props.context.namespacePlaceholder)
const allowedFilterFieldsPlaceholder = computed(() => props.context.allowedFilterFieldsPlaceholder)
const filter = computed(() => props.context.filter ?? true)

// Shared cached query rather than a per-mount fetch: a form renders several of these and
// re-renders remount them, which previously issued one request per mount.
const { databases: fetchedDatabases, databasesAreLoading: isLoading } = useDatabases()
const databases = computed<DatabaseDto[]>(() => fetchedDatabases.value ?? [])

// Get current value from context
const currentValue = computed(() => props.context.value ?? null)

// Selected database (computed property that syncs with the form value)
const selectedDatabase = computed({
  get: () => currentValue.value?.collection_name ?? null,
  set: (value: string | null) => {
    if (value) {
      // When database changes, reset namespaces and allowed filter fields
      emitValue(value, [], [])
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
      emitValue(selectedDatabase.value, value, allowedFilterFields.value)
    }
  },
})

// Allowed metadata filter fields (delegated to ChipsInput child component)
const allowedFilterFields = computed(() => currentValue.value?.allowed_metadata_filter_fields ?? [])

const chipsInputContext = computed(() => ({
  node: {
    input: (value: string[]) => {
      if (selectedDatabase.value) {
        emitValue(selectedDatabase.value, selectedNamespaces.value, value)
      }
    },
  },
  value: allowedFilterFields.value,
  placeholder: allowedFilterFieldsPlaceholder.value ?? t('lib.vectorStore.allowedFilterFields.placeholder'),
  inputId: 'vector-store-filter-fields-input',
}))

// Emit complete value object
function emitValue(collectionName: string, namespaces: string[], allowedFilterFieldKeys: string[]) {
  props.context.node.input({
    collection_name: collectionName,
    index_namespaces: namespaces,
    allowed_metadata_filter_fields: allowedFilterFieldKeys,
  })
}

// Database options for select
const databaseOptions = computed<DatabaseOption[]>(() =>
  databases.value.map(db => ({
    name: db.name,
    displayName: db.display_name || capitalCase(db.name),
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
    displayName: ns.display_name || capitalCase(ns.name),
  }))
})

function getDatabaseDisplayName(name: string): string {
  const option = databaseOptions.value.find(opt => opt.name === name)
  return option?.displayName ?? name
}
</script>
