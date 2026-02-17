<template>
  <StructuralColumn
    :title="t('evaluation.experiment.title')"
    :loading="experimentsAreLoading"
  >
    <div class="flex flex-col gap-2">
      <Message
        v-if="runStarted"
        severity="success"
      >
        <div class="flex items-center gap-4">
          <ProgressSpinner
            class="spinner size-4"
            stroke-width="4"
            fill="transparent"
          />
          <div class="flex flex-row gap-2 font-normal">
            <span class="font-bold">{{ t('evaluation.experiment.running') }}</span>
            <span>{{ t('evaluation.experiment.running_description') }}</span>
          </div>
        </div>
      </Message>
      <Message
        v-if="runHasErrors"
        severity="error"
      >
        <div class="flex flex-row gap-2 font-normal">
          <span class="font-bold">{{ t('evaluation.experiment.failed') }}</span>
          <span>{{ t('evaluation.experiment.failed_description') }}</span>
        </div>
      </Message>
      <div class="flex justify-between">
        <div class="flex gap-2">
          <MultiSelect
            v-model="selectedAgents"
            display="chip"
            show-clear
            :options="filterableAgents"
            option-label="agent_config.name"
            :option-value="(agent: MinimalAgentInstanceDto) => `${agent.agent_class}.${agent.agent_id}`"
            :placeholder="t('evaluation.experiment.filter_by_assistant')"
            :loading="experimentsAreLoading"
          />
          <MultiSelect
            v-model="selectedDatasets"
            display="chip"
            show-clear
            :options="filterableDatasets"
            option-label="dataset_name"
            option-value="id"
            :placeholder="t('evaluation.experiment.filter_by_dataset')"
            :loading="experimentsAreLoading"
          />
        </div>
        <div>
          <Button
            :label="t('evaluation.experiment.run_experiment')"
            icon="pi pi-plus"
            @click="createModalOpen = true"
          />
        </div>
      </div>
      <Dialog
        v-model:visible="createModalOpen"
        modal
        :header="t('evaluation.experiment.create_new')"
      >
        <EvaluationExperimentCreate
          @close="createModalOpen = false"
          @success="onRunExperiment"
        />
      </Dialog>
      <div
        class="grid grid-cols-2 gap-4 xl:grid-cols-2"
      >
        <EvaluationExperimentCard
          v-for="experiment in shownExperiments"
          :key="experiment.id"
          :experiment="experiment"
          @click="() => toExperiment(experiment)"
        />
      </div>
    </div>
  </StructuralColumn>
  <NuxtPage />
</template>

<script setup lang="ts">
import type { MinimalExperiment, MinimalAgentInstanceDto, MinimalDataset } from '@core/sdk/client'

import { useLocalePath } from '#i18n'

const route = useRoute()
const router = useRouter()
const localePath = useLocalePath()
const { t } = useI18n()

const { experiments, experimentsAreLoading } = useExperiments()
const createModalOpen = ref(false)
const runStarted = ref(false)
const runHasErrors = ref(false)
const selectedAgents = useRouteQuery<string[]>('assistants', [], { route, router })
const selectedDatasets = useRouteQuery<string[]>('datasets', [], { route, router })

const toExperiment = (experiment: MinimalExperiment) => {
  router.push(localePath(`/service/evaluations/experiments/${experiment.id}`))
}

const filterableAgents = computed<MinimalAgentInstanceDto[]>(() => {
  if (!experiments.value) {
    return []
  }
  const agents = experiments.value.map((experiment: MinimalExperiment) => {
    return experiment.agent
  })
  return [...new Set(agents)]
})
const filterableDatasets = computed<MinimalDataset[]>(() => {
  if (!experiments.value) {
    return []
  }
  const datasets = experiments.value.map((experiment: MinimalExperiment) => {
    return experiment.dataset
  })
  return [...new Set(datasets)]
})

const shownExperiments = computed<MinimalExperiment[]>(() => {
  if (selectedAgents.value.length === 0 || selectedDatasets.value.length === 0) {
    return experiments.value
  }
  return experiments.value.filter((experiment: MinimalExperiment) => {
    const agentMatch = selectedAgents.value.some((classIdTuple: string) => {
      const [agentClass, agentId] = classIdTuple.split('.')
      return agentClass === experiment.agent.agent_class && agentId === experiment.agent.agent_id
    })
    const datasetMatch = selectedDatasets.value.some((datasetId: string) => {
      return datasetId === experiment.dataset.id
    })
    return agentMatch && datasetMatch
  })
})

const onRunExperiment = (promise: Promise<void>) => {
  runStarted.value = true
  createModalOpen.value = false
  promise
    .then(() => {
      runStarted.value = false
    })
    .catch(() => {
      runStarted.value = false
      runHasErrors.value = true
    })
}
</script>
