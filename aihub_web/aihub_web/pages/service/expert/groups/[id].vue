<template>
  <StructuralScreen>
    <StructuralColumn
      :title="group?.name || t('expert.groups.group_detail')"
      :loading="isLoading"
      :close-route="localePath('/service/expert/groups')"
    >
      <div
        v-if="group"
        class="flex flex-col gap-4"
      >
        <Card>
          <template #title>
            <div class="flex items-center justify-between">
              <span>{{ t('expert.groups.information') }}</span>
              <Button
                icon="pi pi-pencil"
                severity="secondary"
                text
                @click="openEditDialog"
              />
            </div>
          </template>
          <template #content>
            <div class="flex flex-col gap-4">
              <div>
                <label class="mb-2 block text-sm font-semibold">{{ t('expert.groups.name') }}</label>
                <p>{{ group.name }}</p>
              </div>
              <div v-if="group.description">
                <label class="mb-2 block text-sm font-semibold">{{ t('expert.groups.description') }}</label>
                <p class="whitespace-pre-wrap">
                  {{ group.description }}
                </p>
              </div>
              <div>
                <label class="mb-2 block text-sm font-semibold">{{ t('expert.groups.created_at') }}</label>
                <p>{{ formatDate(group.created_at) }}</p>
              </div>
              <div>
                <label class="mb-2 block text-sm font-semibold">{{ t('expert.groups.updated_at') }}</label>
                <p>{{ formatDate(group.updated_at) }}</p>
              </div>
            </div>
          </template>
        </Card>

        <Card>
          <template #title>
            <div class="flex items-center justify-between">
              <span>{{ t('expert.groups.members') }} ({{ group.member_user_ids.length }})</span>
              <Button
                icon="pi pi-plus"
                :label="t('expert.groups.add_member')"
                severity="secondary"
                @click="openAddMemberDialog"
              />
            </div>
          </template>
          <template #content>
            <ExpertGroupMemberList
              :group-id="group.id"
              :member-user-ids="group.member_user_ids"
              @member-removed="refetch"
            />
          </template>
        </Card>
      </div>
    </StructuralColumn>

    <ExpertGroupEditDialog
      v-model:visible="editDialogVisible"
      :group="group"
      @updated="handleGroupUpdated"
    />

    <ExpertGroupAddMemberDialog
      v-model:visible="addMemberDialogVisible"
      :group-id="group?.id || ''"
      @member-added="handleMemberAdded"
    />
  </StructuralScreen>
</template>

<script setup lang="ts">
import { useExpertGroup } from '@core/composables/expert/useExpertGroups'
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'

const { t } = useI18n()
const route = useRoute()
const localePath = useLocalePath()

const groupId = computed(() => route.params.id as string)

const { group, isLoading, refetch } = useExpertGroup(groupId)

const editDialogVisible = ref(false)
const addMemberDialogVisible = ref(false)

const openEditDialog = () => {
  editDialogVisible.value = true
}

const openAddMemberDialog = () => {
  addMemberDialogVisible.value = true
}

const handleGroupUpdated = () => {
  refetch()
}

const handleMemberAdded = () => {
  refetch()
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString()
}
</script>
