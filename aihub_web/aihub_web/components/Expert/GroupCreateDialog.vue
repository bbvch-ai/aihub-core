<template>
  <Dialog
    v-model:visible="visible"
    modal
    :header="t('expert.groups.create_dialog.title')"
    :style="{ width: '50rem' }"
    :breakpoints="{ '1199px': '75vw', '575px': '90vw' }"
  >
    <div class="flex flex-col gap-4">
      <div>
        <label
          for="name"
          class="mb-2 block font-semibold"
        >
          {{ t('expert.groups.name') }} <span class="text-red-500">*</span>
        </label>
        <InputText
          id="name"
          v-model="formData.name"
          class="w-full"
          :placeholder="t('expert.groups.create_dialog.name_placeholder')"
        />
      </div>

      <div>
        <label
          for="description"
          class="mb-2 block font-semibold"
        >
          {{ t('expert.groups.description') }}
        </label>
        <Textarea
          id="description"
          v-model="formData.description"
          :placeholder="t('expert.groups.create_dialog.description_placeholder')"
          rows="4"
          class="w-full"
        />
      </div>
    </div>

    <template #footer>
      <Button
        :label="t('common.cancel')"
        severity="secondary"
        @click="visible = false"
      />
      <Button
        :label="t('expert.groups.create_dialog.create')"
        :loading="isPending"
        :disabled="!formData.name.trim()"
        @click="handleCreate"
      />
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { useCreateExpertGroup } from '@core/composables/expert/useExpertGroups'
import { useToast } from 'primevue/usetoast'
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import type { CreateExpertGroupRequest } from '@core/sdk/client'

const visible = defineModel<boolean>('visible', { default: false })

const emit = defineEmits<{
  created: []
}>()

const { t } = useI18n()
const toast = useToast()

const formData = ref<CreateExpertGroupRequest>({
  name: '',
  description: null,
  member_user_ids: [],
})

const { createGroupAsync, isPending } = useCreateExpertGroup()

watch(visible, (newValue) => {
  if (!newValue) {
    formData.value = {
      name: '',
      description: null,
      member_user_ids: [],
    }
  }
})

const handleCreate = async () => {
  if (!formData.value.name.trim())
    return

  try {
    await createGroupAsync({
      ...formData.value,
      description: formData.value.description?.trim() || null,
    })

    toast.add({
      severity: 'success',
      summary: t('expert.groups.create_dialog.success_title'),
      detail: t('expert.groups.create_dialog.success_message'),
      life: 3000,
    })

    visible.value = false
    emit('created')
  }
  catch {
    toast.add({
      severity: 'error',
      summary: t('expert.groups.create_dialog.error_title'),
      detail: t('expert.groups.create_dialog.error_message'),
      life: 5000,
    })
  }
}
</script>
