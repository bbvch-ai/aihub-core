<script setup lang="ts">
import { useConfirm } from 'primevue/useconfirm'
import { useToast } from 'primevue/usetoast'
import { ref, watch } from 'vue'

import type { MemoryDto } from '@core/sdk/client'

interface Props {
  memory: MemoryDto
}

const props = defineProps<Props>()

const emit = defineEmits<{
  update: [data: string]
  delete: []
  close: []
}>()

const confirm = useConfirm()
const toast = useToast()

const editedData = ref('')
const isEditing = ref(false)

watch(() => props.memory, (newMemory) => {
  editedData.value = newMemory.memory
  isEditing.value = false
}, { immediate: true })

const handleSave = () => {
  if (!editedData.value.trim()) {
    toast.add({
      severity: 'warn',
      summary: 'Validation Error',
      detail: 'Memory content cannot be empty',
      life: 3000,
    })
    return
  }

  emit('update', editedData.value)
  isEditing.value = false
}

const handleCancel = () => {
  editedData.value = props.memory.memory
  isEditing.value = false
}

const handleDelete = () => {
  confirm.require({
    message: 'Are you sure you want to delete this memory? This action cannot be undone.',
    header: 'Delete Memory',
    icon: 'pi pi-exclamation-triangle',
    accept: () => {
      emit('delete')
    },
  })
}
</script>

<template>
  <div class="flex h-full flex-col space-y-4">
    <div class="flex-1 space-y-4 overflow-y-auto">
      <div class="space-y-2">
        <label class="text-xs font-medium text-gray-700 dark:text-gray-500">Memory Content</label>
        <Textarea
          v-if="isEditing"
          v-model="editedData"
          auto-resize
          rows="5"
          class="w-full"
        />
        <div
          v-else
          class="rounded border bg-surface-50 p-3 dark:border-surface-800 dark:bg-surface-950"
        >
          {{ memory.memory }}
        </div>
      </div>

      <div class="grid grid-cols-2 gap-4">
        <div class="space-y-1">
          <label class="text-xs font-medium text-gray-500">Memory ID</label>
          <div class="font-mono text-sm">
            {{ memory.id }}
          </div>
        </div>

        <div class="space-y-1">
          <label class="text-xs font-medium text-gray-500">Score</label>
          <div class="text-sm">
            {{ memory.score != null ? memory.score.toFixed(2) : '-' }}
          </div>
        </div>

        <div class="space-y-1">
          <label class="text-xs font-medium text-gray-500">Agent ID</label>
          <div class="font-mono text-sm">
            {{ memory.agent_id || '-' }}
          </div>
        </div>

        <div class="space-y-1">
          <label class="text-xs font-medium text-gray-500">Thread ID</label>
          <div class="font-mono text-sm">
            {{ memory.thread_id || '-' }}
          </div>
        </div>

        <div class="space-y-1">
          <label class="text-xs font-medium text-gray-500">User ID</label>
          <div class="font-mono text-sm">
            {{ memory.user_id || '-' }}
          </div>
        </div>

        <div class="space-y-1">
          <label class="text-xs font-medium text-gray-500">Created At</label>
          <div class="text-sm">
            {{ new Date(memory.created_at).toLocaleString() }}
          </div>
        </div>
      </div>
    </div>

    <div class="flex items-center justify-between border-t pt-4">
      <Button
        v-if="!isEditing"
        label="Edit"
        icon="pi pi-pencil"
        @click="isEditing = true"
      />
      <div
        v-else
        class="flex space-x-2"
      >
        <Button
          label="Save"
          icon="pi pi-check"
          @click="handleSave"
        />
        <Button
          label="Cancel"
          icon="pi pi-times"
          severity="secondary"
          @click="handleCancel"
        />
      </div>

      <Button
        label="Delete"
        icon="pi pi-trash"
        severity="danger"
        @click="handleDelete"
      />
    </div>
  </div>
</template>

<style scoped>
/* Component uses Tailwind and PrimeVue styles */
</style>
