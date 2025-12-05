<template>
  <StructuralScreen>
    <StructuralColumn
      :title="t('expert.title')"
      :loading="isLoading"
    >
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
    </StructuralColumn>

    <ExpertAnswerDialog
      v-model:visible="answerDialogVisible"
      :question="selectedQuestion"
      @submitted="handleAnswerSubmitted"
    />
  </StructuralScreen>
</template>

<script setup lang="ts">
import {
  useExpertQuestions,
  usePendingExpertQuestionsCount,
} from '@core/composables/expert/useExpertQuestions'
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import type { ExpertQuestionDto } from '@core/composables/expert/useExpertQuestions'

const { t } = useI18n()

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
  isLoading,
  refetch,
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
  refetch()
  refetchCount()
}
</script>
