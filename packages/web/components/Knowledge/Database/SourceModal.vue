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
        @submit="submitSource"
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

async function submitSource(configuration: Record<string, unknown> | null) {
  if (!props.database) return
  isSubmitting.value = true
  try {
    await updateDatabaseSource({
      database: props.database.name,
      tenantId: tenantId.value!,
      request: configuration === null
        ? { source: null, source_configuration: {} }
        : { source: selectedSourceData.value?.name ?? null, source_configuration: configuration },
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
