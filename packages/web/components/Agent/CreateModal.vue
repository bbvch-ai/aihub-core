<template>
  <Dialog
    v-model:visible="visible"
    modal
    :header="t('agent.create.title')"
    :style="{ width: '50rem' }"
    :closable="!isSubmitting"
  >
    <div class="flex flex-col gap-6">
      <div
        v-if="agentClassesAreLoading"
        class="flex items-center justify-center py-8"
      >
        <ProgressSpinner />
      </div>

      <div
        v-else-if="!agentClasses || agentClasses.length === 0"
        class="py-8 text-center text-surface-500"
      >
        {{ t('agent.create.noAgentClasses') }}
      </div>

      <template v-else>
        <div
          v-if="!hasFixedClass"
          class="flex flex-col gap-2"
        >
          <label
            for="agentClass"
            class="text-sm font-medium"
          >
            {{ t('agent.create.selectClass') }}
          </label>
          <Select
            v-model="selectedClass"
            :options="agentClasses"
            option-label="agent_class"
            option-value="agent_class"
            :placeholder="t('agent.create.selectClassPlaceholder')"
            class="w-full"
            :disabled="isSubmitting"
          />
        </div>

        <div
          v-if="selectedClassData && configForm.length > 0 && formReady"
          class="content flex flex-col gap-2"
        >
          <FormKit
            id="create-agent-form"
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
                <Step>{{ t('agent.create.steps.basicInfo') }}</Step>
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
        :label="t('agent.create.cancel')"
        severity="secondary"
        @click="closeModal"
      />
      <Button
        :label="t('agent.create.submit')"
        :disabled="!selectedClass || isSubmitting"
        :loading="isSubmitting"
        @click="triggerFormSubmit"
      />
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { type FormElement, normalizeFormLocaleStrings } from '@core/composables/form/useFormKitTransform'
import { getNode } from '@formkit/core'

const props = defineProps<{
  modelValue: boolean
  initialClass?: string
  initialData?: Record<string, unknown> | null
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'success': [agentClass: string, agentId: string]
}>()

const { t, locale } = useI18n()
const toast = useToast()
const { agentClasses, agentClassesAreLoading } = useAgentClasses()
const { createAgentInstance } = useCreateAgentInstance()
const { tenantId } = useTenant()

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
  cleanFormData,
  coerceNullableToggles,
  applyInitialData,
  resetForm,
} = useCreateInstanceForm({
  classes: agentClasses,
  classField: 'agent_class',
  idField: 'agent_id',
  initialClass: () => props.initialClass ?? '',
  locale,
})

const isSubmitting = ref(false)
const formReady = ref(false)
const hasFixedClass = computed(() => !!props.initialClass)

const visible = computed({
  get: () => props.modelValue,
  set: (value: boolean) => emit('update:modelValue', value),
})

watch(visible, async (isVisible) => {
  if (!isVisible) {
    formReady.value = false
    return
  }
  await nextTick()
  if (props.initialData) {
    applyInitialData(props.initialData)
  }
  formReady.value = true
})

function closeModal() {
  visible.value = false
  resetForm()
}

function triggerFormSubmit() {
  isSubmitting.value = true
  const formNode = getNode('create-agent-form')
  if (formNode) {
    formNode.submit()
  }
  else {
    handleFormSubmit()
  }
}

async function handleFormSubmit() {
  try {
    const cleanedData = cleanFormData(formData.value)
    const coerced = coerceNullableToggles(cleanedData, configForm.value as FormElement[])
    const normalizedConfig = normalizeFormLocaleStrings(coerced)
    const agentId = normalizedConfig.agent_id as string
    await createAgentInstance({
      agentClass: selectedClass.value,
      tenantId: tenantId.value!,
      request: {
        agent_id: agentId,
        configuration: normalizedConfig,
      },
    })

    toast.add({
      severity: 'success',
      summary: t('agent.create.success'),
      life: 3000,
    })

    emit('success', selectedClass.value, agentId)
    closeModal()
  }
  catch (error) {
    console.error('Failed to create agent:', error)
    toast.add({
      severity: 'error',
      summary: t('agent.create.error'),
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

.content :deep(.formkit-group-fieldset) {
}

.content :deep(.formkit-group-fieldset legend) {
  @apply hidden;
}

.content :deep(.formkit-group-fieldset .formkit-group-fieldset) {
}

.content :deep(.formkit-slider-value-input) {
  @apply w-20;
}

.content :deep(.formkit-slider-value-input .p-inputnumber-input) {
  @apply text-center text-sm;
}

.content :deep(#create-agent-form-incomplete) {
  @apply font-bold text-sm text-right pr-2;
}
</style>
