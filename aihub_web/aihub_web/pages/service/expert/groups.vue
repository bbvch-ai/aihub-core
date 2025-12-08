<template>
  <StructuralScreen>
    <StructuralColumn
      :title="t('expert.groups.title')"
      :loading="isLoading"
    >
      <DataView :value="groups">
        <template #header>
          <div class="flex items-center justify-between">
            <h3 class="text-lg font-semibold">
              {{ t('expert.groups.all_groups') }}
            </h3>
            <Button
              :label="t('expert.groups.create_group')"
              icon="pi pi-plus"
              @click="openCreateDialog"
            />
          </div>
        </template>

        <template #list="{ items }">
          <div
            class="flex flex-col gap-4"
            role="list"
          >
            <ExpertGroupCard
              v-for="item in items"
              :key="item.id"
              :group="item"
              @edit="openEditDialog"
              @delete="handleDelete"
              @view="navigateToGroup"
            />
          </div>
        </template>

        <template #empty>
          <div class="flex flex-col items-center justify-center p-8 text-center">
            <i class="pi pi-users p-4 text-xl opacity-70" />
            <p class="text-sm font-light opacity-70">
              {{ t('expert.groups.no_groups') }}
            </p>
            <Button
              :label="t('expert.groups.create_first_group')"
              class="mt-4"
              @click="openCreateDialog"
            />
          </div>
        </template>
      </DataView>
    </StructuralColumn>

    <ExpertGroupCreateDialog
      v-model:visible="createDialogVisible"
      @created="handleGroupCreated"
    />

    <ExpertGroupEditDialog
      v-model:visible="editDialogVisible"
      :group="selectedGroup"
      @updated="handleGroupUpdated"
    />
  </StructuralScreen>
</template>

<script setup lang="ts">
import { useExpertGroups, useDeleteExpertGroup } from '@core/composables/expert/useExpertGroups'
import { useToast } from 'primevue/usetoast'
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import type { ExpertGroupResponse } from '@core/sdk/client'

const { t } = useI18n()
const router = useRouter()
const localePath = useLocalePath()
const toast = useToast()

const { groups, isLoading, refetch } = useExpertGroups()
const { deleteGroupAsync } = useDeleteExpertGroup()

const createDialogVisible = ref(false)
const editDialogVisible = ref(false)
const selectedGroup = ref<ExpertGroupResponse | null>(null)

const openCreateDialog = () => {
  createDialogVisible.value = true
}

const openEditDialog = (group: ExpertGroupResponse) => {
  selectedGroup.value = group
  editDialogVisible.value = true
}

const navigateToGroup = (group: ExpertGroupResponse) => {
  router.push(localePath(`/service/expert/groups/${group.id}`))
}

const handleDelete = async (group: ExpertGroupResponse) => {
  try {
    await deleteGroupAsync(group.id)
    toast.add({
      severity: 'success',
      summary: t('expert.groups.delete_success_title'),
      detail: t('expert.groups.delete_success_message'),
      life: 3000,
    })
    refetch()
  }
  catch {
    toast.add({
      severity: 'error',
      summary: t('expert.groups.delete_error_title'),
      detail: t('expert.groups.delete_error_message'),
      life: 5000,
    })
  }
}

const handleGroupCreated = () => {
  refetch()
}

const handleGroupUpdated = () => {
  refetch()
}
</script>
