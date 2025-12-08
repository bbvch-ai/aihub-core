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
          for="user-select"
          class="mb-2 block font-semibold"
        >
          {{ t('expert.groups.add_member_dialog.user') }} <span class="text-red-500">*</span>
        </label>
        <Select
          id="user-select"
          v-model="selectedUserId"
          :options="availableUsers"
          option-value="id"
          filter
          :placeholder="t('expert.groups.add_member_dialog.select_user')"
          :loading="usersAreLoading"
          class="w-full"
        >
          <template #value="{ value }">
            <div
              v-if="value"
              class="flex items-center gap-2"
            >
              <span>{{ getUserDisplayName(value) }}</span>
            </div>
            <span v-else>{{ t('expert.groups.add_member_dialog.select_user') }}</span>
          </template>
          <template #option="{ option }">
            <div class="flex flex-col">
              <span class="font-medium">{{ option.name }}</span>
              <span class="text-sm opacity-70">{{ option.email }}</span>
            </div>
          </template>
        </Select>
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
        :disabled="!selectedUserId"
        @click="handleAddMember"
      />
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { useAddGroupMember } from '@core/composables/expert/useExpertGroups'
import useUsers from '@core/composables/user/useUsers'
import { useToast } from 'primevue/usetoast'
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

const props = defineProps<{
  groupId: string
  existingMemberIds: string[]
}>()

const visible = defineModel<boolean>('visible', { default: false })

const emit = defineEmits<{
  memberAdded: []
}>()

const { t } = useI18n()
const toast = useToast()

const selectedUserId = ref<string | null>(null)

const { users, usersAreLoading } = useUsers()
const { addMemberAsync, isPending } = useAddGroupMember()

const availableUsers = computed(() => {
  return users.value.filter(user => !props.existingMemberIds.includes(user.id))
})

const getUserDisplayName = (userId: string) => {
  const user = users.value.find(u => u.id === userId)
  return user ? `${user.name} (${user.email})` : userId
}

watch(visible, (newValue) => {
  if (!newValue) {
    selectedUserId.value = null
  }
})

const handleAddMember = async () => {
  if (!selectedUserId.value)
    return

  try {
    await addMemberAsync({
      groupId: props.groupId,
      userId: selectedUserId.value,
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
