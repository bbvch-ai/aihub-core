<template>
  <StructuralScreen>
    <StructuralColumn :title="t('expert.title')">
      <TabView v-model:active-index="activeTabIndex">
        <!-- Questions Tab -->
        <TabPanel>
          <template #header>
            <div class="flex items-center gap-2">
              <span>{{ t('expert.tabs.questions') }}</span>
              <Badge
                v-if="pendingCount > 0"
                :value="pendingCount"
                severity="danger"
              />
            </div>
          </template>

          <div :class="{ 'pointer-events-none opacity-50': isLoadingQuestions }">
            <DataView
              :value="questions"
              paginator
              :rows="pageSize"
              :total-records="totalRecords"
              :first="(currentPage - 1) * pageSize"
              lazy
              @page="onPage"
            >
              <template #header>
                <div class="flex flex-col justify-between gap-4 sm:flex-row">
                  <div class="flex items-center gap-2">
                    <Badge
                      :value="pendingCount"
                      severity="danger"
                    />
                    <span class="font-semibold">{{ t('expert.pending_questions') }}</span>
                  </div>
                  <div class="flex gap-2">
                    <SelectButton
                      v-model="activeFilter"
                      :options="filterOptions"
                      option-label="label"
                      option-value="value"
                      :allow-empty="false"
                      :aria-label="t('expert.filter_questions')"
                    />
                  </div>
                </div>
              </template>

              <template #list="{ items }">
                <div
                  class="flex flex-col"
                  role="list"
                >
                  <ExpertQuestionItem
                    v-for="item in items"
                    :key="item.id"
                    :question="item"
                    @answer="openAnswerDialog"
                  />
                </div>
              </template>

              <template #empty>
                <div class="flex flex-col items-center justify-center p-8 text-center">
                  <i class="pi pi-check-circle p-4 text-xl opacity-70" />
                  <p class="text-sm font-light opacity-70">
                    {{ getEmptyStateTitle }}
                  </p>
                </div>
              </template>
            </DataView>
          </div>
        </TabPanel>

        <!-- Groups Tab -->
        <TabPanel>
          <template #header>
            <span>{{ t('expert.tabs.groups') }}</span>
          </template>
          <div :class="{ 'pointer-events-none opacity-50': isLoadingGroups }">
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
          </div>
        </TabPanel>
      </TabView>
    </StructuralColumn>

    <!-- Questions Tab Dialogs -->
    <ExpertAnswerDialog
      v-model:visible="answerDialogVisible"
      :question="selectedQuestion"
      @submitted="handleAnswerSubmitted"
    />

    <!-- Groups Tab Dialogs -->
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
import {
  useExpertQuestions,
  usePendingExpertQuestionsCount,
} from '@core/composables/expert/useExpertQuestions'
import { useToast } from 'primevue/usetoast'
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'

import type { ExpertQuestionDto } from '@core/composables/expert/useExpertQuestions'
import type { ExpertGroupResponse } from '@core/sdk/client'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const localePath = useLocalePath()
const toast = useToast()

// Tab management
const activeTabIndex = ref(0)
const tabToIndex: Record<string, number> = { questions: 0, groups: 1 }
const indexToTab = ['questions', 'groups']

// Initialize from URL
onMounted(() => {
  const tab = route.query.tab as string
  if (tab && tab in tabToIndex) {
    activeTabIndex.value = tabToIndex[tab]
  }
})

// Update URL when tab changes
watch(activeTabIndex, (newIndex) => {
  const tab = indexToTab[newIndex]
  if (route.query.tab !== tab) {
    router.replace({ query: { ...route.query, tab } })
  }
})

// Update tab when URL changes (browser back/forward)
watch(() => route.query.tab, (newTab) => {
  if (newTab && newTab in tabToIndex) {
    const index = tabToIndex[newTab as string]
    if (activeTabIndex.value !== index) {
      activeTabIndex.value = index
    }
  }
})

// Questions Tab State
const currentPage = ref(1)
const pageSize = ref(10)
const statusFilter = ref<string | undefined>('pending')

const filterOptions = computed(() => [
  { label: t('expert.filter.pending'), value: 'pending' },
  { label: t('expert.filter.answered'), value: 'answered' },
  { label: t('expert.filter.all'), value: undefined },
])

const activeFilter = ref('pending')

const {
  questions,
  isLoading: isLoadingQuestions,
  refetch: refetchQuestions,
  totalRecords,
} = useExpertQuestions({
  currentPage,
  pageSize,
  filters: {
    status: statusFilter,
  },
})

const { count: pendingCount, refetch: refetchCount } = usePendingExpertQuestionsCount()

watch(() => activeFilter.value, (newFilter) => {
  statusFilter.value = newFilter === 'all' ? undefined : newFilter
  currentPage.value = 1
}, { immediate: true })

const onPage = (event: { page: number, rows: number }) => {
  currentPage.value = event.page + 1
  pageSize.value = event.rows
}

const getEmptyStateTitle = computed(() => {
  const titles: Record<string, string> = {
    pending: t('expert.no_pending_questions'),
    answered: t('expert.no_answered_questions'),
    all: t('expert.no_questions'),
  }
  return titles[activeFilter.value] || titles.all
})

const answerDialogVisible = ref(false)
const selectedQuestion = ref<ExpertQuestionDto | null>(null)

const openAnswerDialog = (question: ExpertQuestionDto) => {
  selectedQuestion.value = question
  answerDialogVisible.value = true
}

const handleAnswerSubmitted = () => {
  refetchQuestions()
  refetchCount()
}

// Groups Tab State
const { groups, isLoading: isLoadingGroups, refetch: refetchGroups } = useExpertGroups()
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
    refetchGroups()
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
  refetchGroups()
}

const handleGroupUpdated = () => {
  refetchGroups()
}
</script>
