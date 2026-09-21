<template>
  <Dialog
    v-model:visible="isOpen"
    :header="t('support.dialog_title')"
    modal
    :style="{ width: '44rem' }"
    :breakpoints="{ '1199px': '80vw', '767px': '95vw' }"
  >
    <div
      v-if="incidentFormIsLoading"
      class="flex justify-center py-10"
    >
      <ProgressSpinner style="width: 2rem; height: 2rem" />
    </div>

    <Message
      v-else-if="incidentFormError"
      severity="warn"
      :closable="false"
    >
      {{ t('support.unavailable') }}
    </Message>

    <template v-else-if="incidentForm">
      <FormKitDynamicConfiguration
        :form="incidentForm.elements"
        :initial-data="initialData"
        :submit-label="incidentIsSubmitting ? t('support.submitting') : t('support.submit')"
        @submit="onSubmit"
      >
        <template #before-submit>
          <div
            v-if="incidentForm.attachments"
            class="flex flex-col gap-2 border-b border-surface-200 pb-4 dark:border-surface-700"
          >
            <label class="font-medium">{{ incidentForm.attachments.label }}</label>
            <p
              v-if="incidentForm.attachments.description"
              class="text-xs font-light text-surface-500 dark:text-surface-400"
            >
              {{ incidentForm.attachments.description }}
            </p>
            <FileUpload
              mode="basic"
              multiple
              custom-upload
              :auto="false"
              :accept="incidentForm.attachments.accept.join(',')"
              :file-limit="incidentForm.attachments.max_files"
              :max-file-size="incidentForm.attachments.max_bytes"
              :choose-label="t('support.choose_files')"
              @select="onSelect"
            />
            <ul
              v-if="attachments.length"
              class="flex flex-col gap-1 text-xs text-surface-600 dark:text-surface-300"
            >
              <li
                v-for="file in attachments"
                :key="file.name"
                class="flex items-center gap-2"
              >
                <i class="pi pi-paperclip" />
                <span>{{ file.name }}</span>
                <span class="text-surface-400">{{ Math.ceil(file.size / 1024) }} KB</span>
              </li>
            </ul>
          </div>
        </template>
      </FormKitDynamicConfiguration>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
const { t } = useI18n()
const toast = useToast()
const { isOpen, close } = useIncidentReport()
const { incidentForm, incidentFormIsLoading, incidentFormError } = useIncidentForm()
const { submitIncident, incidentIsSubmitting } = useSubmitIncident()
const { buildIncidentContext } = useIncidentContext()

// Snapshotted when the dialog opens rather than computed: the reported time has to be when the
// reporter raised this, and DynamicConfiguration seeds its model from `initialData` only once.
const initialData = ref<Record<string, string>>({})
const attachments = ref<File[]>([])

watch(isOpen, (opened) => {
  if (!opened) return
  initialData.value = buildIncidentContext()
  attachments.value = []
})

function onSelect(event: { files: File[] }): void {
  attachments.value = event.files
}

async function onSubmit(submission: Record<string, unknown>): Promise<void> {
  try {
    const created = await submitIncident({ submission, attachments: attachments.value })
    toast.add({
      severity: 'success',
      summary: t('support.sent'),
      detail: t('support.sent_detail', { reference: created.reference, number: created.number }),
      life: 8000,
    })
    close()
  }
  catch {
    // Left open on purpose: the dialog still holds everything the reporter typed, so closing it
    // would make them write the report twice.
    toast.add({ severity: 'error', summary: t('support.send_failed'), detail: t('support.send_failed_detail') })
  }
}
</script>
