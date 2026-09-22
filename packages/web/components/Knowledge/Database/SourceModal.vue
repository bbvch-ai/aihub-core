<template>
  <Dialog
    v-model:visible="visible"
    modal
    :header="t('knowledge.form.edit_source.title', { name: database?.display_name || database?.name })"
    :style="{ width: '50rem' }"
    :closable="!isSubmitting"
  >
    <div class="flex flex-col gap-6">
      <div class="flex flex-col gap-2">
        <label
          for="database-source-edit-select"
          class="text-sm font-medium"
        >
          {{ t('knowledge.form.source.label') }}
        </label>
        <Select
          id="database-source-edit-select"
          v-model="selectedSource"
          :options="sourceOptions"
          option-label="display_name"
          option-value="name"
          :disabled="isSubmitting"
          class="w-full"
        />
        <small class="text-gray-500">
          {{ selectedSourceData?.description || t('knowledge.form.source.manual_upload.description') }}
        </small>
      </div>

      <!-- Keyed on the source so switching re-seeds the form: the stored configuration only applies to the
           source it was written for, and its secrets arrive masked and stay masked unless replaced. -->
      <FormKitDynamicConfiguration
        v-if="selectedSourceData"
        :key="selectedSourceData.name"
        :form="selectedSourceData.form"
        :initial-data="initialConfiguration"
        @submit="confirmHandoverThenSubmit"
      />
      <Button
        v-else
        :label="t('knowledge.form.edit_source.switch_to_manual')"
        :loading="isSubmitting"
        :disabled="database?.source === null"
        class="w-full"
        @click="submitSource(null)"
      />
    </div>
  </Dialog>
</template>

<script setup lang="ts">
import type { DatabaseDto, SourcePipelineDto } from '@core/sdk/client'

const MANUAL_UPLOAD = '__manual_upload__'

const props = defineProps<{
  modelValue: boolean
  database: DatabaseDto | null
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const { t } = useI18n()
const toast = useToast()
const confirm = useConfirm()
const { tenantId } = useTenant()
const { sourcePipelines } = useSourcePipelines()
const { mutateAsync: updateDatabaseSource } = useUpdateDatabaseSource()

const isSubmitting = ref(false)
const selectedSource = ref<string>(MANUAL_UPLOAD)

const visible = computed({
  get: () => props.modelValue,
  set: (value: boolean) => emit('update:modelValue', value),
})

const sourceOptions = computed<Array<Pick<SourcePipelineDto, 'name' | 'display_name' | 'description'>>>(() => [
  {
    name: MANUAL_UPLOAD,
    display_name: t('knowledge.form.source.manual_upload.label'),
    description: t('knowledge.form.source.manual_upload.description'),
  },
  ...(sourcePipelines.value ?? []),
])
const selectedSourceData = computed<SourcePipelineDto | undefined>(() =>
  sourcePipelines.value?.find(source => source.name === selectedSource.value),
)

// The stored configuration is only meaningful for the source it belongs to; another source starts blank.
const initialConfiguration = computed<Record<string, unknown>>(() =>
  props.database?.source === selectedSource.value
    ? (props.database?.source_configuration ?? {}) as Record<string, unknown>
    : {},
)

watch(visible, (isVisible) => {
  if (!isVisible) return
  selectedSource.value = props.database?.source ?? MANUAL_UPLOAD
})

// A source owns its database's content: on the next sync it removes every file it does not have. Handing a
// manually filled database over is therefore confirmed first, and the API refuses it without the acknowledgement.
const existingDocuments = computed(() =>
  (props.database?.namespaces ?? []).reduce((total, namespace) => total + namespace.number_of_documents, 0),
)
const isHandoverFromManualUpload = computed(() => props.database?.source === null && existingDocuments.value > 0)

function confirmHandoverThenSubmit(configuration: Record<string, unknown>) {
  if (!isHandoverFromManualUpload.value) {
    submitSource(configuration)
    return
  }
  confirm.require({
    header: t('knowledge.form.edit_source.replace_documents.header'),
    message: t('knowledge.form.edit_source.replace_documents.message', {
      name: props.database?.display_name || props.database?.name,
      count: existingDocuments.value,
    }),
    icon: 'pi pi-exclamation-triangle',
    rejectLabel: t('common.actions.cancel'),
    acceptLabel: t('knowledge.form.edit_source.replace_documents.accept'),
    acceptClass: 'p-button-danger',
    accept: () => submitSource(configuration, { replaceExistingDocuments: true }),
  })
}

async function submitSource(
  configuration: Record<string, unknown> | null,
  options: { replaceExistingDocuments?: boolean } = {},
) {
  if (!props.database) return
  isSubmitting.value = true
  try {
    await updateDatabaseSource({
      database: props.database.name,
      tenantId: tenantId.value!,
      request: configuration === null
        ? { source: null, source_configuration: {} }
        : {
            source: selectedSourceData.value?.name ?? null,
            source_configuration: configuration,
            replace_existing_documents: options.replaceExistingDocuments ?? false,
          },
    })
    toast.add({ severity: 'success', summary: t('knowledge.form.edit_source.success'), life: 3000 })
    visible.value = false
  }
  catch (error) {
    console.error('Failed to update the knowledge database source:', error)
    toast.add({
      severity: 'error',
      summary: t('knowledge.form.edit_source.error'),
      detail: error instanceof Error ? error.message : String(error),
      life: 5000,
    })
  }
  finally {
    isSubmitting.value = false
  }
}
</script>
