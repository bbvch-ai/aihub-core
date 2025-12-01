<template>
  <StructuralColumn
    v-if="selectedMemory"
    :close-route="'/service/memories/list'"
    title="Memory Details"
  >
    <MemoryEdit
      :memory="selectedMemory"
      @update="handleUpdate"
      @delete="handleDelete"
      @close="emit('close')"
    />
  </StructuralColumn>
</template>

<script setup lang="ts">
const route = useRoute()

defineProps<{
  selectedMemoryId?: string
}>()

const emit = defineEmits<{
  close: []
  update: [memoryId: string, data: string]
  delete: [memoryId: string]
}>()

const { paginatedMemories } = useMemories()

const selectedMemory = computed(() => {
  const memoryId = route.params.memory_id as string
  return paginatedMemories.value.find(m => m.id === memoryId)
})

const handleUpdate = (data: string) => {
  if (selectedMemory.value) {
    emit('update', selectedMemory.value.id, data)
  }
}

const handleDelete = () => {
  if (selectedMemory.value) {
    emit('delete', selectedMemory.value.id)
  }
}
</script>
