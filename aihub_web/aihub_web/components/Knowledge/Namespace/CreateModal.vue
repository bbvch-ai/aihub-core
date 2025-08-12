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
        <label class="text-sm font-medium">{{ t('knowledge.form.database.label') }}</label>
        <Dropdown
          v-model="selectedDatabase"
          :options="databaseOptions"
          option-label="name"
          option-value="name"
          :placeholder="t('knowledge.form.database.placeholder')"
          :class="{ 'p-invalid': error }"
          class="w-full"
        />
      </div>

      <div class="flex flex-col gap-2">
        <label class="text-sm font-medium">{{ t('knowledge.form.folder_name.label') }}</label>
        <InputText
          v-model="name"
          :placeholder="t('knowledge.form.folder_name.placeholder')"
          :class="{ 'p-invalid': error }"
        />
        <small class="text-gray-500">{{ t('knowledge.form.folder_name.help') }}</small>
      </div>

      <div class="flex flex-col gap-2">
        <label class="text-sm font-medium">{{ t('knowledge.form.display_name.label') }}</label>
        <InputText
          v-model="displayName"
          :placeholder="t('knowledge.form.display_name.placeholder')"
        />
        <small class="text-gray-500">{{ t('knowledge.form.display_name.help') }}</small>
      </div>

      <div class="flex flex-col gap-2">
        <label class="text-sm font-medium">{{ t('knowledge.form.description.label') }}</label>
        <Textarea
          v-model="description"
          :placeholder="t('knowledge.form.description.placeholder')"
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
import type { CreateNamespaceRequest, DatabaseDto } from '@core/sdk/client'

import { useI18n } from '#i18n'

const props = defineProps<{
  modelValue: boolean
  databases: DatabaseDto[]
  initialDatabase?: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'success': [data: { database: string, namespace: string }]
}>()

const { t } = useI18n()
const { mutateAsync: createNamespace, isPending: isCreating } = useCreateNamespace()

const selectedDatabase = ref('')
const name = ref('')
const displayName = ref('')
const description = ref('')
const error = ref('')

const databaseOptions = computed(() => props.databases || [])
const canSubmit = computed(() => selectedDatabase.value.trim() && name.value.trim())

const closeModal = () => {
  emit('update:modelValue', false)
}

const resetForm = () => {
  selectedDatabase.value = ''
  name.value = ''
  displayName.value = ''
  description.value = ''
  error.value = ''
}

const handleCreate = async () => {
  if (!canSubmit.value) return

  const requestBody: CreateNamespaceRequest = {
    database_name: selectedDatabase.value,
    namespace_name: name.value,
    folder_name: name.value,
    display_name: displayName.value,
    description: description.value,
  }

  await createNamespace(ref(requestBody))
  emit('success', { database: selectedDatabase.value, namespace: name.value })
  closeModal()
}

watch(() => props.modelValue, (isVisible) => {
  if (isVisible) {
    selectedDatabase.value = props.initialDatabase || ''
  }
})
</script>
