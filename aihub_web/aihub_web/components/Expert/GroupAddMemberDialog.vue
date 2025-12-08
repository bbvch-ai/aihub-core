<template>
  <Dialog
    v-model:visible="visible"
    modal
    :header="t('expert.groups.add_member_dialog.title')"
    :style="{ width: '30rem' }"
    :breakpoints="{ '1199px': '75vw', '575px': '90vw' }"
  >
    <div class="flex flex-col gap-4">
      <div>
        <label
          for="user-id"
          class="mb-2 block font-semibold"
        >
          {{ t('expert.groups.add_member_dialog.user_id') }} <span class="text-red-500">*</span>
        </label>
        <InputText
          id="user-id"
          v-model="userId"
          class="w-full"
          :placeholder="t('expert.groups.add_member_dialog.user_id_placeholder')"
        />
        <small class="mt-1 block opacity-70">
          {{ t('expert.groups.add_member_dialog.user_id_hint') }}
        </small>
      </div>
    </div>

    <template #footer>
      <Button
        :label="t('common.cancel')"
        severity="secondary"
        @click="visible = false"
      />
      <Button
        :label="t('expert.groups.add_member_dialog.add')"
        :loading="isPending"
        :disabled="!userId.trim()"
        @click="handleAddMember"
      />
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { useAddGroupMember } from '@core/composables/expert/useExpertGroups'
import { useToast } from 'primevue/usetoast'
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

const props = defineProps<{
  groupId: string
}>()

const visible = defineModel<boolean>('visible', { default: false })

const emit = defineEmits<{
  memberAdded: []
}>()

const { t } = useI18n()
const toast = useToast()

const userId = ref('')

const { addMemberAsync, isPending } = useAddGroupMember()

watch(visible, (newValue) => {
  if (!newValue) {
    userId.value = ''
  }
})

const handleAddMember = async () => {
  if (!userId.value.trim())
    return

  try {
    await addMemberAsync({
      groupId: props.groupId,
      userId: userId.value.trim(),
    })

    toast.add({
      severity: 'success',
      summary: t('expert.groups.add_member_dialog.success_title'),
      detail: t('expert.groups.add_member_dialog.success_message'),
      life: 3000,
    })

    visible.value = false
    emit('memberAdded')
  }
  catch {
    toast.add({
      severity: 'error',
      summary: t('expert.groups.add_member_dialog.error_title'),
      detail: t('expert.groups.add_member_dialog.error_message'),
      life: 5000,
    })
  }
}
</script>
