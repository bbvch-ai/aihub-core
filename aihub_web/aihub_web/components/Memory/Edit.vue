<script setup lang="ts">
import Avatar from 'primevue/avatar'
import { useConfirm } from 'primevue/useconfirm'
import { useToast } from 'primevue/usetoast'
import { computed, ref, watch } from 'vue'

import type { MemoryDto } from '@core/sdk/client'

import { useLocalePath } from '#i18n'

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
const { t } = useI18n()
const router = useRouter()
const localePath = useLocalePath()

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
    rejectProps: {
      label: 'Cancel',
      severity: 'secondary',
      outlined: true,
    },
    acceptProps: {
      label: 'Delete',
      severity: 'danger',
    },
    accept: () => {
      emit('delete')
    },
  })
}

// Parse agent_id from "agent_class/agent_id" format
const parsedAgent = computed(() => {
  if (!props.memory.agent_id) return null
  const parts = props.memory.agent_id.split('/')
  if (parts.length !== 2) return null
  return { agent_class: parts[0], agent_id: parts[1] }
})

// Check if we can navigate to agent
const canNavigateToAgent = computed(() => parsedAgent.value !== null)

// Check if we can navigate to thread/display (both must exist)
const canNavigateToThread = computed(() => {
  return !!props.memory.thread_id && !!props.memory.display_id
})

// Construct agent URL
const agentUrl = computed(() => {
  if (!parsedAgent.value) return ''
  return `/service/agents/${parsedAgent.value.agent_class}-${parsedAgent.value.agent_id}/overview`
})

// Construct thread/display URL
const threadDisplayUrl = computed(() => {
  if (!canNavigateToThread.value) return ''
  return `/service/threads/${props.memory.thread_id}/display/${props.memory.display_id}`
})

const navigateToAgent = () => {
  if (canNavigateToAgent.value) {
    router.push(localePath(agentUrl.value))
  }
}

const navigateToThreadDisplay = () => {
  if (canNavigateToThread.value) {
    router.push(localePath(threadDisplayUrl.value))
  }
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

      <div class="space-y-4">
        <!-- Created At - always shown -->
        <div class="space-y-2">
          <label class="text-xs font-medium text-gray-500">
            {{ t('memory.detail.created_at') }}
          </label>
          <div class="text-sm">
            {{ new Date(memory.created_at).toLocaleString() }}
          </div>
        </div>

        <!-- Agent Link - shown if agent exists -->
        <!-- Follows the AgentAvatar pattern from Thread/Info.vue but simplified -->
        <div
          v-if="canNavigateToAgent"
          class="space-y-2"
        >
          <label class="text-xs font-medium text-gray-500">
            {{ t('memory.detail.agent_link_label') }}
          </label>
          <div
            class="flex cursor-pointer gap-2 rounded border border-surface-200 p-2 hover:bg-surface-100 dark:border-surface-800 hover:dark:bg-surface-800"
            @click="navigateToAgent"
          >
            <Avatar
              size="normal"
              icon="pi pi-verified"
            />
            <div class="mb-1 flex flex-col justify-center">
              <p class="text-xs font-bold">
                {{ parsedAgent.agent_class }}
              </p>
              <p class="text-xs">
                {{ parsedAgent.agent_class }} / {{ parsedAgent.agent_id }}
              </p>
            </div>
          </div>
        </div>

        <!-- Thread/Display Link - shown if both thread_id and display_id exist -->
        <!-- Similar pattern to agent but with thread/conversation icon -->
        <div
          v-if="canNavigateToThread"
          class="space-y-2"
        >
          <label class="text-xs font-medium text-gray-500">
            {{ t('memory.detail.thread_link_label') }}
          </label>
          <div
            class="flex cursor-pointer gap-2 rounded border border-surface-200 p-2 hover:bg-surface-100 dark:border-surface-800 hover:dark:bg-surface-800"
            @click="navigateToThreadDisplay"
          >
            <Avatar
              size="normal"
              icon="pi pi-comments"
            />
            <div class="mb-1 flex flex-col justify-center">
              <p class="text-xs font-bold">
                {{ t('memory.detail.thread_title') }}
              </p>
              <p class="font-mono text-xs">
                {{ memory.thread_id?.substring(0, 8) }}... / {{ memory.display_id?.substring(0, 8) }}...
              </p>
            </div>
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
