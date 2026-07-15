<template>
  <Dialog
    :visible="modelValue"
    modal
    :header="t('knowledge.form.create_database.title')"
    :style="{ width: '35rem' }"
    @update:visible="emit('update:modelValue', $event)"
    @hide="resetForm"
  >
    <div class="flex flex-col gap-4">
      <div class="flex flex-col gap-2">
        <label
          for="database-name-input"
          class="text-sm font-medium"
        >
          {{ t('knowledge.form.database_name.label') }}
          <span class="ml-1 text-xs text-red-500">*</span>
        </label>
        <InputText
          v-model="name"
          input-id="database-name-input"
          :placeholder="t('knowledge.form.database_name.placeholder')"
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
        >{{ t('knowledge.form.database_name.help') }}</small>
      </div>

      <div class="flex flex-col gap-2">
        <label
          for="database-display-name-input"
          class="text-sm font-medium"
        >
          {{ t('knowledge.form.display_name.label') }}
          <span class="ml-1 text-xs text-gray-400">(optional)</span>
        </label>
        <InputText
          v-model="displayName"
          input-id="database-display-name-input"
          :placeholder="t('knowledge.form.display_name.placeholder')"
          :disabled="isCreating"
        />
        <small class="text-gray-500">{{ t('knowledge.form.display_name.help') }}</small>
      </div>

      <div class="flex flex-col gap-2">
        <label
          for="database-description-textarea"
          class="text-sm font-medium"
        >
          {{ t('knowledge.form.description.label') }}
          <span class="ml-1 text-xs text-gray-400">(optional)</span>
        </label>
        <Textarea
          v-model="description"
          input-id="database-description-textarea"
          :placeholder="t('knowledge.form.description.placeholder')"
          :disabled="isCreating"
          rows="3"
        />
        <small class="text-gray-500">{{ t('knowledge.form.description.help') }}</small>
      </div>

      <div class="flex flex-col gap-2">
        <label
          for="database-ingestor-select"
          class="text-sm font-medium"
        >
          {{ t('knowledge.form.ingestor.label') }}
          <span class="ml-1 text-xs text-red-500">*</span>
        </label>
        <Select
          v-model="ingestor"
          input-id="database-ingestor-select"
          :options="ingestors"
          option-label="display_name"
          option-value="name"
          :placeholder="t('knowledge.form.ingestor.placeholder')"
          :loading="ingestorsAreLoading"
          :disabled="isCreating"
          class="w-full"
        />
        <small class="text-gray-500">
          {{ selectedIngestorDescription || t('knowledge.form.ingestor.help') }}
        </small>
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
import type { CreateDatabaseRequest, IngestorType } from '@core/sdk/client'

const { t } = useI18n()

defineProps<{
  modelValue: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'success': [data: { database: string }]
}>()

const { mutateAsync: createDatabase } = useCreateDatabase()
const { ingestors, ingestorsAreLoading } = useIngestors()
const { tenantId } = useTenant()

const name = ref('')
const displayName = ref('')
const description = ref('')
const ingestor = ref<IngestorType | undefined>()
const error = ref('')
const isCreating = ref(false)

const defaultIngestor = computed(() => ingestors.value?.[0]?.name as IngestorType | undefined)

const selectedIngestorDescription = computed(
  () => ingestors.value?.find(candidate => candidate.name === ingestor.value)?.description,
)

watch(defaultIngestor, (fallback) => {
  ingestor.value ??= fallback
}, { immediate: true })

const nameValidationError = computed(() => {
  if (!name.value.trim()) return ''

  const namePattern = /^[a-zA-Z0-9]+$/
  if (!namePattern.test(name.value)) {
    return t('knowledge.form.database_name.validation_error')
  }

  return ''
})

const canSubmit = computed(() => name.value.trim() && ingestor.value && !nameValidationError.value && !isCreating.value)

const closeModal = () => {
  emit('update:modelValue', false)
}

const resetForm = () => {
  name.value = ''
  displayName.value = ''
  description.value = ''
  ingestor.value = defaultIngestor.value
  error.value = ''
  isCreating.value = false
}

const handleCreate = async () => {
  if (!canSubmit.value) return

  isCreating.value = true
  error.value = ''

  const requestBody: CreateDatabaseRequest & { database: string, tenantId: string } = {
    database: name.value,
    display_name: displayName.value,
    description: description.value,
    ingestor: ingestor.value,
    tenantId: tenantId.value!,
  }

  await createDatabase(requestBody)
  emit('success', { database: name.value })
  closeModal()
}
</script>
