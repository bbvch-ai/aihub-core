<template>
  <div>
    <MultiSelect
      v-model="selectedDatabases"
      :options="databaseOptions"
      option-label="displayName"
      option-value="name"
      :placeholder="placeholder ?? t('common.selectDatabases')"
      :filter="filter"
      display="chip"
      class="w-full"
      :loading="isLoading"
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
    </MultiSelect>
  </div>
</template>

<script setup lang="ts">
import { capitalCase } from 'change-case'

import type { DatabaseDto } from '@core/sdk/client'

interface DatabaseOption {
  name: string
  displayName: string
}

interface KnowledgeDatabaseSelectorProps {
  context: {
    node: { input: (value: string[] | null) => void }
    value?: string[] | null
    placeholder?: string
    filter?: boolean
  }
}

const props = defineProps<KnowledgeDatabaseSelectorProps>()
const { t } = useI18n()

const placeholder = computed(() => props.context.placeholder)
const filter = computed(() => props.context.filter ?? true)

// Shared cached query rather than a per-mount fetch: a form renders several of these and
// re-renders remount them, which previously issued one request per mount.
const { databases: fetchedDatabases, databasesAreLoading: isLoading } = useDatabases()
const databases = computed<DatabaseDto[]>(() => fetchedDatabases.value ?? [])

const selectedDatabases = computed({
  get: () => props.context.value ?? [],
  set: (value: string[]) => {
    props.context.node.input(value.length > 0 ? value : null)
  },
})

const databaseOptions = computed<DatabaseOption[]>(() =>
  databases.value.map(db => ({
    name: db.name,
    displayName: db.display_name || capitalCase(db.name),
  })),
)
</script>
