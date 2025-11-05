<template>
  <Dialog
    :visible="modelValue"
    modal
    :header="t('knowledge.form.create.title')"
    :style="{ width: '35rem' }"
    @update:visible="emit('update:modelValue', $event)"
    @hide="resetForm"
  >
    <div class="flex flex-col gap-4">
      <div class="flex flex-col gap-2">
        <label class="text-sm font-medium">
          {{ t('knowledge.form.database.label') }}
          <span class="ml-1 text-xs text-red-500">*</span>
        </label>
        <Dropdown
          v-model="selectedDatabase"
          :options="databaseOptions"
          option-label="displayName"
          option-value="name"
          :placeholder="t('knowledge.form.database.placeholder')"
          :class="{ 'p-invalid': error }"
          :disabled="isCreating"
          class="w-full"
        />
      </div>

      <div class="flex flex-col gap-2">
        <label class="text-sm font-medium">
          {{ t('knowledge.form.folder_name.label') }}
          <span class="ml-1 text-xs text-red-500">*</span>
        </label>
        <InputText
          v-model="name"
          :placeholder="t('knowledge.form.folder_name.placeholder')"
          :class="{ 'p-invalid': error || nameValidationError }"
          :disabled="isCreating"
        />
        <small
          v-if="nameValidationError"
          class="text-red-500"
        >{{ nameValidationError }}</small>
        <small
          v-else
          class="text-gray-500"
        >{{ t('knowledge.form.folder_name.help') }}</small>
      </div>

      <div class="flex flex-col gap-2">
        <label class="text-sm font-medium">
          {{ t('knowledge.form.display_name.label') }}
          <span class="ml-1 text-xs text-gray-400">(optional)</span>
        </label>
        <InputText
          v-model="displayName"
          :placeholder="t('knowledge.form.display_name.placeholder')"
          :disabled="isCreating"
        />
        <small class="text-gray-500">{{ t('knowledge.form.display_name.help') }}</small>
      </div>

      <div class="flex flex-col gap-2">
        <label class="text-sm font-medium">
          {{ t('knowledge.form.description.label') }}
          <span class="ml-1 text-xs text-gray-400">(optional)</span>
        </label>
        <Textarea
          v-model="description"
          :placeholder="t('knowledge.form.description.placeholder')"
          :disabled="isCreating"
          rows="3"
        />
        <small class="text-gray-500">{{ t('knowledge.form.description.help') }}</small>
      </div>

      <small
        v-if="error"
        class="text-red-500"
      >{{ error }}</small>
    </div>
    <template #footer>
      <div class="flex justify-end gap-2">
        <Button
          :label="t('knowledge.actions.cancel')"
          severity="secondary"
          outlined
          @click="closeModal"
        />
        <Button
          :label="t('knowledge.actions.create')"
          :disabled="!canSubmit"
          :loading="isCreating"
          @click="handleCreate"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { useChangeCase } from '@vueuse/integrations/useChangeCase'

import type { CreateNamespaceRequest, DatabaseDto } from '@core/sdk/client'

const { t } = useI18n()

const props = defineProps<{
  modelValue: boolean
  databases: DatabaseDto[]
  initialDatabase?: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'success': [data: { database: string, namespace: string }]
}>()

const { mutateAsync: createNamespace } = useCreateNamespace()

const selectedDatabase = ref('')
const name = ref('')
const displayName = ref('')
const description = ref('')
const error = ref('')
const isCreating = ref(false)

const databaseOptions = computed(() =>
  (props.databases || [])
    .filter(db => !db.auto_sync)
    .map(db => ({
      name: db.name,
      displayName: useChangeCase(db.name, 'capitalCase'),
    })),
)
const nameValidationError = computed(() => {
  if (!name.value.trim()) return ''

  const namePattern = /^[a-zA-Z0-9_-]+$/
  if (!namePattern.test(name.value)) {
    return t('knowledge.form.folder_name.validation_error')
  }

  return ''
})

const canSubmit = computed(() => selectedDatabase.value.trim() && name.value.trim() && !nameValidationError.value && !isCreating.value)

const closeModal = () => {
  emit('update:modelValue', false)
}

const resetForm = () => {
  selectedDatabase.value = ''
  name.value = ''
  displayName.value = ''
  description.value = ''
  error.value = ''
  isCreating.value = false
}

const handleCreate = async () => {
  if (!canSubmit.value) return

  isCreating.value = true
  error.value = ''

  const requestBody: CreateNamespaceRequest & { database: string, namespace: string } = {
    database: selectedDatabase.value,
    namespace: name.value,
    folder_name: name.value,
    display_name: displayName.value,
    description: description.value,
  }

  await createNamespace(requestBody)
  emit('success', { database: selectedDatabase.value, namespace: name.value })
  closeModal()
}

watch(() => props.modelValue, (isVisible) => {
  if (isVisible) {
    selectedDatabase.value = props.initialDatabase || ''
  }
})
</script>
