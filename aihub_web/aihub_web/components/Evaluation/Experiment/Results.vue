<template>
  <div class="flex flex-col gap-4">
    <span class="mb-4 block text-sm text-surface-500 dark:text-surface-400">
      {{ experiment.description }}
    </span>
    <Panel
      class="panel pt-5"
    >
      <div class="grid grid-cols-2 gap-4 xl:grid-cols-4">
        <div class="flex flex-col items-start gap-2">
          <span class="font-semibold">
            {{ t('evaluation.experiment.language_and_dataset') }}
          </span>
          <div class="flex gap-2">
            <Tag
              severity="secondary"
              :value="t(`languages.${experiment.locale}`)"
            />
            <Tag
              severity="contrast"
              :value="experiment.dataset.dataset_name"
            />
          </div>
        </div>
        <div class="flex flex-col items-start gap-2">
          <span class="font-semibold">
            {{ t('evaluation.experiment.result.correctness') }}
          </span>
          <Rating :model-value="useRound((experiment.correctness?.avg_score ?? 0) * 5)" />
        </div>
        <div class="flex flex-col items-start gap-2">
          <span class="font-semibold">
            {{ t('evaluation.experiment.result.completeness') }}
          </span>
          <Rating :model-value="useRound((experiment.completeness?.avg_score ?? 0) * 5)" />
        </div>
        <div class="flex flex-col items-start gap-2">
          <span class="font-semibold">
            {{ t('evaluation.experiment.result.conciseness') }}
          </span>
          <Rating :model-value="useRound((experiment.conciseness?.avg_score ?? 0) * 5)" />
        </div>
      </div>
    </Panel>
    <DataTable
      v-model:expanded-rows="expandedRows"
      data-key="example_id"
      removable-sort
      size="small"
      :value="experiment.items"
    >
      <Column
        expander
        class="max-w-8"
      />
      <Column
        class="max-w-48 truncate"
        field="question"
        :header="t('evaluation.experiment.result.question')"
      />
      <Column
        class="max-w-48 truncate"
        field="reference_answer"
        :header="t('evaluation.experiment.result.reference_answer')"
      />
      <Column
        field="assistant_answer"
        :header="t('evaluation.experiment.result.assistant_answer')"
      />
      <Column
        sortable
        class="max-w-32"
        field="correctness.score"
        :header="t('evaluation.experiment.result.correctness')"
      >
        <template #body="{ data }">
          <Rating :model-value="useRound((data.correctness?.score ?? 0) * 5)" />
        </template>
      </Column>
      <Column
        sortable
        class="max-w-32"
        field="completeness.score"
        :header="t('evaluation.experiment.result.completeness')"
      >
        <template #body="{ data }">
          <Rating :model-value="useRound((data.completeness?.score ?? 0) * 5)" />
        </template>
      </Column>
      <Column
        sortable
        class="max-w-32"
        field="conciseness.score"
        :header="t('evaluation.experiment.result.conciseness')"
      >
        <template #body="{ data }">
          <Rating :model-value="useRound((data.conciseness?.score ?? 0) * 5)" />
        </template>
      </Column>
      <Column
        sortable
        class="max-w-24"
        field="latency_ms"
        :header="t('evaluation.experiment.result.latency_ms')"
      >
        <template #body="{ data }">
          <Tag
            :value="useRound(data.latency_ms / 1000).value + ' s'"
            :severity="latencySeverity(data.latency_ms)"
          />
        </template>
      </Column>
      <Column
        class="max-w-24"
        field="thread_id"
        header=""
      >
        <template #body="{ data }">
          <Button
            size="small"
            rounded
            icon="pi pi-search"
            severity="secondary"
            @click="() => toTrace(data)"
          />
        </template>
      </Column>
      <template #expansion="{ data }">
        <div class="flex flex-col gap-3 pl-10">
          <p>
            <span class="font-bold">{{ t('evaluation.experiment.result.question') }}: </span> {{ data.question }}
          </p>
          <p>
            <span class="font-bold">{{ t('evaluation.experiment.result.reference_answer') }}: </span> {{ data.reference_answer }}
          </p>
          <p>
            <span class="font-bold">{{ t('evaluation.experiment.result.assistant_answer') }}: </span> {{ data.assistant_answer }}
          </p>
          <p>
            <span class="font-bold">{{ t('evaluation.experiment.result.correctness') }} </span> {{ data.correctness?.explanation }}
          </p>
          <p>
            <span class="font-bold">{{ t('evaluation.experiment.result.completeness') }} </span> {{ data.completeness?.explanation }}
          </p>
          <p>
            <span class="font-bold">{{ t('evaluation.experiment.result.conciseness') }} </span> {{ data.conciseness?.explanation }}
          </p>
        </div>
      </template>
    </DataTable>
  </div>
</template>

<script setup lang="ts">
import type { Experiment, ExperimentRunRecord } from '@core/sdk/client'

defineProps<{
  experiment: Experiment
}>()

const { t } = useI18n()
const router = useRouter()
const localeRoute = useLocaleRoute()

const expandedRows = ref({})

const latencySeverity = (latency_ms: number) => {
  if (latency_ms > 30_000) {
    return 'danger'
  }
  if (latency_ms > 10_000) {
    return 'warning'
  }
  return 'success'
}

const toTrace = (data: ExperimentRunRecord) => {
  router.push(localeRoute(`/service/threads/${data.thread_id}/display/${data.display_id}`))
}
</script>

<style scoped>
.panel :deep(.p-panel-header) {
  padding: 0 !important;
}
</style>
