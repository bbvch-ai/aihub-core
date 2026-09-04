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
import { type FormElement, serializeFormData } from '@core/composables/form/useFormKitTransform'
import { getNode } from '@formkit/core'

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
  initialClass: () => '',
  locale,
})

const databaseName = ref('')
const isSubmitting = ref(false)
const formReady = ref(false)

const visible = computed({
  get: () => props.modelValue,
  set: (value: boolean) => emit('update:modelValue', value),
})

watch(ingestors, (available) => {
  if (!selectedClass.value && available?.length) {
    selectedClass.value = available[0].name
  }
}, { immediate: true })

watch(visible, async (isVisible) => {
  if (!isVisible) {
    formReady.value = false
    return
  }
  await nextTick()
  formReady.value = true
})

const nameValidationError = computed(() => {
  if (!databaseName.value.trim()) return ''
  if (!/^[a-zA-Z][a-zA-Z0-9]*$/.test(databaseName.value)) {
    return t('knowledge.form.database_name.validation_error')
  }
  return ''
})

const canSubmit = computed(
  () => databaseName.value.trim() && selectedClass.value && !nameValidationError.value && !isSubmitting.value,
)

function closeModal() {
  visible.value = false
  databaseName.value = ''
  resetForm()
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
  try {
    await createDatabase({
      database,
      tenantId: tenantId.value!,
      request: {
        ingestor: selectedClass.value,
        configuration: serializeFormData(formData.value, configForm.value as FormElement[]),
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
