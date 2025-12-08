<template>
  <Card class="cursor-pointer hover:bg-surface-50 dark:hover:bg-surface-800">
    <template #content>
      <div
        class="flex items-start justify-between"
        @click="$emit('view', group)"
      >
        <div class="flex-1">
          <div class="mb-2 flex items-center gap-2">
            <i class="pi pi-users text-primary" />
            <h4 class="text-lg font-semibold">
              {{ group.name }}
            </h4>
          </div>
          <p
            v-if="group.description"
            class="mb-3 text-sm opacity-70"
          >
            {{ group.description }}
          </p>
          <div class="flex items-center gap-4 text-sm opacity-70">
            <div class="flex items-center gap-1">
              <i class="pi pi-user text-xs" />
              <span>{{ group.member_user_ids.length }} {{ t('expert.groups.members') }}</span>
            </div>
            <div class="flex items-center gap-1">
              <i class="pi pi-calendar text-xs" />
              <span>{{ t('expert.groups.created') }} {{ formatDate(group.created_at) }}</span>
            </div>
          </div>
        </div>
        <div class="flex gap-2">
          <Button
            icon="pi pi-pencil"
            severity="secondary"
            text
            rounded
            @click.stop="$emit('edit', group)"
          />
          <Button
            icon="pi pi-trash"
            severity="danger"
            text
            rounded
            @click.stop="confirmDelete"
          />
        </div>
      </div>
    </template>
  </Card>
</template>

<script setup lang="ts">
import { useConfirm } from 'primevue/useconfirm'
import { useI18n } from 'vue-i18n'

import type { ExpertGroupResponse } from '@core/sdk/client'

const props = defineProps<{
  group: ExpertGroupResponse
}>()

const emit = defineEmits<{
  edit: [group: ExpertGroupResponse]
  delete: [group: ExpertGroupResponse]
  view: [group: ExpertGroupResponse]
}>()

const { t } = useI18n()
const confirm = useConfirm()

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString()
}

const confirmDelete = () => {
  confirm.require({
    message: t('expert.groups.delete_confirm_message', { name: props.group.name }),
    header: t('expert.groups.delete_confirm_title'),
    icon: 'pi pi-exclamation-triangle',
    rejectLabel: t('common.cancel'),
    acceptLabel: t('common.delete'),
    accept: () => {
      emit('delete', props.group)
    },
  })
}
</script>
