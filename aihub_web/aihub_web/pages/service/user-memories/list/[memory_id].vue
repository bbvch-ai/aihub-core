<template>
  <StructuralColumn
    v-if="selectedMemory"
    :close-route="'/service/user-memories/list'"
    child-column
    title="Memory Details"
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
const route = useRoute()

// Create user memory composables using factory
const { useMemories, useUpdateMemory, useDeleteMemory } = createMemoryComposables({
  type: 'user',
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
  closeRoute: '/service/user-memories/list',
})
</script>
