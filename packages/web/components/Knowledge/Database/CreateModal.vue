<template>
  <Dialog
    v-model:visible="visible"
    modal
    :header="t('knowledge.form.create_database.title')"
    :style="{ width: '50rem' }"
    :closable="!isSubmitting"
  >
    <div class="flex flex-col gap-6">
      <div
        v-if="ingestorsAreLoading"
        class="flex items-center justify-center py-8"
      >
        <ProgressSpinner />
      </div>

      <div
        v-else-if="!ingestors || ingestors.length === 0"
        class="py-8 text-center text-surface-500"
      >
        {{ t('knowledge.form.create_database.no_ingestors') }}
      </div>

      <template v-else>
        <div class="flex flex-col gap-2">
          <label
            for="database-name-input"
            class="text-sm font-medium"
          >
            {{ t('knowledge.form.database_name.label') }}
            <span class="ml-1 text-xs text-red-500">*</span>
          </label>
          <InputText
            id="database-name-input"
            v-model="databaseName"
            :placeholder="t('knowledge.form.database_name.placeholder')"
            :class="{ 'p-invalid': nameValidationError }"
            :disabled="isSubmitting"
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
            for="database-ingestor-select"
            class="text-sm font-medium"
          >
            {{ t('knowledge.form.ingestor.label') }}
            <span class="ml-1 text-xs text-red-500">*</span>
          </label>
          <Select
            id="database-ingestor-select"
            v-model="selectedClass"
            :options="ingestors"
            option-label="display_name"
            option-value="name"
            :placeholder="t('knowledge.form.ingestor.placeholder')"
            :disabled="isSubmitting"
            class="w-full"
          />
          <small class="text-gray-500">
            {{ selectedClassData?.description || t('knowledge.form.ingestor.help') }}
          </small>
        </div>

        <div class="flex flex-col gap-2">
          <label
            for="database-source-select"
            class="text-sm font-medium"
          >
            {{ t('knowledge.form.source.label') }}
          </label>
          <Select
            id="database-source-select"
            v-model="selectedSource"
            :options="sourceOptions"
            option-label="display_name"
            option-value="name"
            :placeholder="t('knowledge.form.source.placeholder')"
            :disabled="isSubmitting"
            class="w-full"
          />
          <small class="text-gray-500">
            {{ selectedSourceData?.description || t('knowledge.form.source.help') }}
          </small>
        </div>

        <div
          v-if="selectedClassData && configForm.length > 0 && formReady"
          class="content flex flex-col gap-2"
        >
          <FormKit
            id="create-database-form"
            v-model="formData"
            type="form"
            :actions="false"
            :config="{
              validationVisibility: 'dirty',
            }"
            @submit="handleFormSubmit"
            @submit-invalid="isSubmitting = false"
          >
            <Stepper
              v-model:value="activeStep"
              orientation="vertical"
            >
              <StepItem
                v-if="simpleElementsSchema.length > 0"
                :value="0"
              >
                <Step>{{ t('knowledge.form.create_database.steps.basic_info') }}</Step>
                <StepPanel>
                  <div class="flex flex-col gap-6 py-4">
                    <FormKitSchema
                      :schema="simpleElementsSchema"
                      :data="formData"
                    />
                  </div>
                </StepPanel>
              </StepItem>
              <StepItem
                v-for="(group, index) in groupConfigs"
                :key="`group-${group.name}`"
                :value="getGroupStepIndex(index)"
              >
                <Step>{{ group.label || group.name }}</Step>
                <StepPanel>
                  <div class="content py-4">
                    <FormKitSchema
                      :schema="group.schema"
                      :data="formData"
                    />
                  </div>
                </StepPanel>
              </StepItem>
              <StepItem
                v-for="(rep, index) in repeaterConfigs"
                :key="`repeater-${rep.path}`"
                :value="getRepeaterStepIndex(index)"
              >
                <Step>{{ rep.label || rep.name }}</Step>
                <StepPanel>
                  <div class="py-4">
                    <FormKitRepeater
                      :model-value="getRepeaterData(rep.path)"
                      :name="rep.name"
                      :label="rep.label"
                      :add-label="rep.addLabel"
                      :children-schema="rep.childrenSchema"
                      :default-item="rep.defaultItem"
                      :min="rep.min"
                      :max="rep.max"
                      @update:model-value="setRepeaterData(rep.path, $event)"
                    />
                  </div>
                </StepPanel>
              </StepItem>
              <StepItem
                v-if="selectedSourceData && sourceSchema.length > 0"
                :value="sourceStepIndex"
              >
                <Step>{{ t('knowledge.form.create_database.steps.source') }}</Step>
                <StepPanel>
                  <div class="content flex flex-col gap-6 py-4">
                    <FormKitSchema
                      :schema="sourceSchema"
                      :data="formData"
                    />
                  </div>
                </StepPanel>
              </StepItem>
            </Stepper>
          </FormKit>
        </div>
      </template>
    </div>

    <template #footer>
      <Button
        :label="t('knowledge.actions.cancel')"
        severity="secondary"
        outlined
        @click="closeModal"
      />
      <Button
        :label="t('knowledge.actions.create')"
        :disabled="!canSubmit"
        :loading="isSubmitting"
        @click="triggerFormSubmit"
      />
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import {
  buildFormKitSchema,
  type FormElement,
  hydrateFormData,
  serializeFormData,
} from '@core/composables/form/useFormKitTransform'
import { getNode } from '@formkit/core'

import type { SourcePipelineDto } from '@core/sdk/client'
import type { FormKitSchemaNode } from '@formkit/core'

// Manual upload is the absence of a source; it is offered as a first, form-less entry of the source list.
const MANUAL_UPLOAD = '__manual_upload__'

const props = defineProps<{
  modelValue: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'success': [data: { database: string }]
}>()

const { t, locale } = useI18n()
const toast = useToast()
const { mutateAsync: createDatabase } = useCreateDatabase()
const { ingestors, ingestorsAreLoading } = useIngestors()
const { sourcePipelines } = useSourcePipelines()
const { tenantId } = useTenant()

// The ingestor list is the "class" list: each ingestor announces the form its databases are configured
// through, exactly as an agent class does, so the agent create flow is reused as is.
const {
  selectedClass,
  formData,
  activeStep,
  selectedClassData,
  configForm,
  simpleElementsSchema,
  groupConfigs,
  repeaterConfigs,
  getGroupStepIndex,
  getRepeaterStepIndex,
  getRepeaterData,
  setRepeaterData,
  resetForm,
} = useCreateInstanceForm({
  classes: ingestors,
  classField: 'name',
  idField: 'name',
  initialClass: () => ingestors.value?.[0]?.name ?? '',
  locale,
})

// The source is a second axis of the database: its form is announced by the source pipeline exactly like the
// ingestor's, and rendered as one more step of the same form under the `source_configuration` group, so a single
// submit carries both.
const selectedSource = ref<string>(MANUAL_UPLOAD)
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
const sourceForm = computed<FormElement[]>(() => (selectedSourceData.value?.form ?? []) as FormElement[])
const sourceSchema = computed<FormKitSchemaNode[]>(() => {
  if (sourceForm.value.length === 0) return []
  return [{
    $formkit: 'group',
    name: 'source_configuration',
    children: buildFormKitSchema(sourceForm.value, { locale: locale.value }),
  }]
})
const sourceStepIndex = computed(
  () => (simpleElementsSchema.value.length > 0 ? 1 : 0) + groupConfigs.value.length + repeaterConfigs.value.length,
)

watch(selectedSource, () => {
  formData.value = {
    ...formData.value,
    source_configuration: sourceForm.value.length > 0 ? hydrateFormData({}, sourceForm.value) : undefined,
  }
})

const databaseName = ref('')
const isSubmitting = ref(false)
const formReady = ref(false)

const visible = computed({
  get: () => props.modelValue,
  set: (value: boolean) => emit('update:modelValue', value),
})

watch(visible, async (isVisible) => {
  if (!isVisible) {
    formReady.value = false
    databaseName.value = ''
    selectedSource.value = MANUAL_UPLOAD
    resetForm()
    return
  }
  await nextTick()
  formReady.value = true
})

const nameValidationError = computed(() => {
  if (!databaseName.value.trim()) return ''

  const namePattern = /^[a-z][a-z0-9]{2,62}$/
  if (!namePattern.test(databaseName.value)) {
    return t('knowledge.form.database_name.validation_error')
  }
  return ''
})

const canSubmit = computed(
  () => databaseName.value.trim() && selectedClass.value && !nameValidationError.value && !isSubmitting.value,
)

function closeModal() {
  visible.value = false
}

function triggerFormSubmit() {
  if (!canSubmit.value) return
  isSubmitting.value = true
  const formNode = getNode('create-database-form')
  if (formNode) {
    formNode.submit()
  }
  else {
    handleFormSubmit()
  }
}

async function handleFormSubmit() {
  const database = databaseName.value
  const { source_configuration, ...ingestorData } = formData.value
  try {
    await createDatabase({
      database,
      tenantId: tenantId.value!,
      request: {
        ingestor: selectedClass.value,
        configuration: serializeFormData(ingestorData, configForm.value as FormElement[]),
        source: selectedSourceData.value?.name ?? null,
        source_configuration: selectedSourceData.value
          ? serializeFormData((source_configuration ?? {}) as Record<string, unknown>, sourceForm.value)
          : {},
      },
    })

    toast.add({
      severity: 'success',
      summary: t('knowledge.form.create_database.success'),
      life: 3000,
    })

    emit('success', { database })
    closeModal()
  }
  catch (error) {
    console.error('Failed to create knowledge database:', error)
    toast.add({
      severity: 'error',
      summary: t('knowledge.form.create_database.error'),
      detail: error instanceof Error ? error.message : String(error),
      life: 5000,
    })
  }
  finally {
    isSubmitting.value = false
  }
}
</script>

<style scoped>
.content {
  @apply font-light text-xs
}

.content :deep(.formkit-group-fieldset) {
  @apply flex flex-col gap-6;
}

.content :deep(.formkit-outer) {
  @apply pt-3 pb-1;
}

.content :deep(.formkit-group-fieldset legend) {
  @apply hidden;
}

.content :deep(#create-database-form-incomplete) {
  @apply font-bold text-sm text-right pr-2;
}
</style>
