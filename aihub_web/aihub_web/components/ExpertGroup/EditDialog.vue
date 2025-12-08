<template>
  <Dialog
    v-model:visible="visible"
    modal
    :header="t('expert.groups.edit_dialog.title')"
    :style="{ width: '50rem' }"
    :breakpoints="{ '1199px': '75vw', '575px': '90vw' }"
  >
    <div
      v-if="group"
      class="flex flex-col gap-4"
    >
      <div>
        <label
          for="edit-name"
          class="mb-2 block font-semibold"
        >
          {{ t('expert.groups.name') }} <span class="text-red-500">*</span>
        </label>
        <InputText
          id="edit-name"
          v-model="formData.name"
          class="w-full"
          :placeholder="t('expert.groups.edit_dialog.name_placeholder')"
        />
      </div>

      <div>
        <label
          for="edit-description"
          class="mb-2 block font-semibold"
        >
          {{ t('expert.groups.description') }}
        </label>
        <Textarea
          id="edit-description"
          v-model="formData.description"
          :placeholder="t('expert.groups.edit_dialog.description_placeholder')"
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
        :label="t('expert.groups.edit_dialog.save')"
        :loading="isPending"
        :disabled="!formData.name?.trim()"
        @click="handleUpdate"
      />
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { useUpdateExpertGroup } from '@core/composables/expert/useExpertGroups'
import { useToast } from 'primevue/usetoast'
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import type { ExpertGroupResponse, UpdateExpertGroupRequest } from '@core/sdk/client'

const props = defineProps<{
  group: ExpertGroupResponse | null
}>()

const visible = defineModel<boolean>('visible', { default: false })

const emit = defineEmits<{
  updated: []
}>()

const { t } = useI18n()
const toast = useToast()

const formData = ref<UpdateExpertGroupRequest>({
  name: '',
  description: null,
})

const { updateGroupAsync, isPending } = useUpdateExpertGroup()

watch(() => props.group, (newGroup) => {
  if (newGroup) {
    formData.value = {
      name: newGroup.name,
      description: newGroup.description,
    }
  }
}, { immediate: true })

watch(visible, (newValue) => {
  if (!newValue && props.group) {
    formData.value = {
      name: props.group.name,
      description: props.group.description,
    }
  }
})

const handleUpdate = async () => {
  if (!props.group || !formData.value.name?.trim())
    return

  try {
    await updateGroupAsync({
      groupId: props.group.id,
      groupData: {
        ...formData.value,
        description: formData.value.description?.trim() || null,
      },
    })

    toast.add({
      severity: 'success',
      summary: t('expert.groups.edit_dialog.success_title'),
      detail: t('expert.groups.edit_dialog.success_message'),
      life: 3000,
    })

    visible.value = false
    emit('updated')
  }
  catch {
    toast.add({
      severity: 'error',
      summary: t('expert.groups.edit_dialog.error_title'),
      detail: t('expert.groups.edit_dialog.error_message'),
      life: 5000,
    })
  }
}
</script>
