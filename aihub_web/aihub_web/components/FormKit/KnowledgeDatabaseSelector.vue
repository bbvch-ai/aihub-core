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
import { getDatabases } from '@core/sdk/client'
import { useChangeCase } from '@vueuse/integrations/useChangeCase'

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

const databases = ref<DatabaseDto[]>([])
const isLoading = ref(false)

const selectedDatabases = computed({
  get: () => props.context.value ?? [],
  set: (value: string[]) => {
    props.context.node.input(value.length > 0 ? value : null)
  },
})

const databaseOptions = computed<DatabaseOption[]>(() =>
  databases.value.map(db => ({
    name: db.name,
    displayName: db.display_name || useChangeCase(db.name, 'capitalCase').value,
  })),
)

async function fetchDatabases() {
  isLoading.value = true
  try {
    const response = await getDatabases({
      composable: '$fetch',
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

onMounted(() => {
  fetchDatabases()
})
</script>
