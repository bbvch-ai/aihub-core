<template>
  <Dialog
    :visible="modelValue"
    modal
    :header="t('knowledge.form.edit.title')"
    :style="{ width: '35rem' }"
    @update:visible="emit('update:modelValue', $event)"
  >
    <div class="flex flex-col gap-4">
      <div class="flex flex-col gap-2">
        <label class="text-sm font-medium">
          {{ t('knowledge.form.folder_name.label') }}
        </label>
        <InputText
          :value="namespace?.name || ''"
          disabled
          class="bg-surface-100 dark:bg-surface-800"
        />
        <small class="text-gray-500">{{ t('knowledge.form.folder_name.edit_help') }}</small>
      </div>

      <div class="flex flex-col gap-2">
        <label class="text-sm font-medium">
          {{ t('knowledge.form.display_name.label') }}
          <span class="ml-1 text-xs text-gray-400">(optional)</span>
        </label>
        <InputText
          v-model="displayName"
          :placeholder="t('knowledge.form.display_name.placeholder')"
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
          :label="t('knowledge.actions.save')"
          @click="handleSave"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import type { NamespaceDto, UpdateNamespaceRequest } from '@core/sdk/client'

import { useI18n } from '#i18n'

const props = defineProps<{
  modelValue: boolean
  namespace: NamespaceDto | null
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'success': []
}>()

const { t } = useI18n()
const { mutateAsync: updateNamespace } = useUpdateNamespace()

const displayName = ref('')
const description = ref('')
const error = ref('')

const closeModal = () => {
  emit('update:modelValue', false)
}

const handleSave = async () => {
  if (!props.namespace) return

  error.value = ''

  const namespaceId = props.namespace.id
  const databaseId = props.namespace.database_id
  const updatePayload: UpdateNamespaceRequest = {
    display_name: displayName.value || props.namespace.name,
    description: description.value || null,
  }

  await updateNamespace({
    namespace: namespaceId,
    database: databaseId,
    payload: ref(updatePayload),
  })

  emit('success')
  closeModal()
}

watch(() => props.namespace, (newNamespace) => {
  if (newNamespace) {
    displayName.value = newNamespace.display_name || newNamespace.name
    description.value = newNamespace.description || ''
    error.value = ''
  }
})
</script>
