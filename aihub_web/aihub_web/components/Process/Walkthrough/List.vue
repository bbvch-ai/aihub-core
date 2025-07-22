<template>
  <DataTable
    :value="walkthroughs"
    table-style="min-width: 50rem"
    selection-mode="single"
    @update:selection="emit('selected', $event)"
  >
    <Column
      field="process_class"
      :header="t('process.walkthrough.list.name')"
    />
  </DataTable>
</template>

<script setup lang="ts">
import type { ProcessWalkthroughDto } from '@core/sdk/client'

defineProps<{
  walkthroughs: ProcessWalkthroughDto[]
}>()

const { t } = useI18n()

const emit = defineEmits<{
  selected: [walkthrough: ProcessWalkthroughDto]
}>()
</script>
