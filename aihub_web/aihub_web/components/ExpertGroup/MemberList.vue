<template>
  <div class="flex flex-col gap-2">
    <div
      v-if="memberUserIds.length === 0"
      class="flex items-center justify-center p-4 text-center"
    >
      <p class="text-sm opacity-70">
        {{ t('expert.groups.no_members') }}
      </p>
    </div>
    <div
      v-for="userId in memberUserIds"
      :key="userId"
      class="flex items-center justify-between rounded-lg border p-3"
    >
      <div class="flex items-center gap-2">
        <i class="pi pi-user text-primary" />
        <span class="font-medium">{{ userId }}</span>
      </div>
      <Button
        icon="pi pi-times"
        severity="danger"
        text
        rounded
        size="small"
        @click="confirmRemove(userId)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRemoveGroupMember } from '@core/composables/expert/useExpertGroups'
import { useConfirm } from 'primevue/useconfirm'
import { useToast } from 'primevue/usetoast'
import { useI18n } from 'vue-i18n'

const props = defineProps<{
  groupId: string
  memberUserIds: string[]
}>()

const emit = defineEmits<{
  memberRemoved: []
}>()

const { t } = useI18n()
const toast = useToast()
const confirm = useConfirm()

const { removeMemberAsync } = useRemoveGroupMember()

const confirmRemove = (userId: string) => {
  confirm.require({
    message: t('expert.groups.remove_member_confirm_message', { userId }),
    header: t('expert.groups.remove_member_confirm_title'),
    icon: 'pi pi-exclamation-triangle',
    rejectLabel: t('common.cancel'),
    acceptLabel: t('common.remove'),
    accept: async () => {
      try {
        await removeMemberAsync({ groupId: props.groupId, userId })
        toast.add({
          severity: 'success',
          summary: t('expert.groups.remove_member_success_title'),
          detail: t('expert.groups.remove_member_success_message'),
          life: 3000,
        })
        emit('memberRemoved')
      }
      catch {
        toast.add({
          severity: 'error',
          summary: t('expert.groups.remove_member_error_title'),
          detail: t('expert.groups.remove_member_error_message'),
          life: 5000,
        })
      }
    },
  })
}
</script>
