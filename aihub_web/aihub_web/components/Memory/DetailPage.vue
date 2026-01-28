<template>
  <StructuralColumn
    v-if="selectedMemory"
    :close-route="closeRoute"
    child-column
    :title="t('memory.detail.title')"
  >
    <MemoryEdit
      :memory="selectedMemory"
      @update="handleUpdate"
      @delete="handleDelete"
      @close="handleClose"
    />
  </StructuralColumn>
</template>

<script setup lang="ts">
const props = defineProps<{
  memoryType: 'user' | 'organization'
}>()

const { t } = useI18n()
const route = useRoute()

const closeRoute = computed(() => `/service/${props.memoryType}-memories/list`)

// Create memory composables using factory based on type
const { useMemories, useUpdateMemory, useDeleteMemory } = createMemoryComposables({
  type: props.memoryType,
})

const { paginatedMemories } = useMemories()
const { updateMemory } = useUpdateMemory()
const { deleteMemory } = useDeleteMemory()

const selectedMemory = computed(() => {
  const memoryId = route.params.memory_id as string
  return paginatedMemories.value.find(m => m.id === memoryId)
})

// Use shared CRUD composable
const { handleUpdate, handleDelete, handleClose } = useMemoryCRUD({
  selectedMemory,
  updateMemory,
  deleteMemory,
  closeRoute: closeRoute.value,
})
</script>
