<template>
  <StructuralColumn
    v-if="selectedMemory"
    :close-route="'/service/memories/list'"
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
import { useToast } from 'primevue/usetoast'

import { useLocalePath } from '#i18n'

const route = useRoute()
const router = useRouter()
const localePath = useLocalePath()
const { t } = useI18n()
const toast = useToast()

const { paginatedMemories } = useMemories()
const { updateMemory } = useUpdateMemory()
const { deleteMemory } = useDeleteMemory()

const selectedMemory = computed(() => {
  const memoryId = route.params.memory_id as string
  return paginatedMemories.value.find(m => m.id === memoryId)
})

const handleClose = () => {
  router.push(localePath('/service/memories/list'))
}

const handleUpdate = async (data: string) => {
  if (!selectedMemory.value) return

  try {
    await updateMemory({ memoryId: selectedMemory.value.id, data })
    toast.add({
      severity: 'success',
      summary: t('memory.update.success.title'),
      detail: t('memory.update.success.message'),
      life: 3000,
    })
  }
  catch (error) {
    console.error('Failed to update memory:', error)
    toast.add({
      severity: 'error',
      summary: t('memory.update.error.title'),
      detail: t('memory.update.error.message'),
      life: 5000,
    })
  }
}

const handleDelete = async () => {
  if (!selectedMemory.value) return

  try {
    await deleteMemory({ memoryId: selectedMemory.value.id })
    toast.add({
      severity: 'success',
      summary: t('memory.delete.success.title'),
      detail: t('memory.delete.success.message'),
      life: 3000,
    })
    // Navigate back to list after successful deletion
    handleClose()
  }
  catch (error) {
    console.error('Failed to delete memory:', error)
    toast.add({
      severity: 'error',
      summary: t('memory.delete.error.title'),
      detail: t('memory.delete.error.message'),
      life: 5000,
    })
  }
}
</script>
