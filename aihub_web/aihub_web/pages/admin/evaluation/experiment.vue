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
            class="spinner color-white size-4"
            stroke-width="4"
            fill="transparent"
          />
          <div class="flex flex-row gap-2 font-normal">
            <span class="font-bold">Experiment is running!</span>
            <span>This might take several minutes. You can also leave this page and come back later.</span>
          </div>
        </div>
      </Message>
      <Message
        v-if="runHasErrors"
        severity="error"
      >
        <div class="flex flex-row gap-2 font-normal">
          <span class="font-bold">Experiment Failed!</span>
          <span>Please contact AI-Hub dev team to find out what went wrong.</span>
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
            :option-value="(agent: MinimalAgentDto) => `${agent.agent_class}.${agent.agent_id}`"
            placeholder="Filter by Assistant"
            :loading="experimentsAreLoading"
          />
          <MultiSelect
            v-model="selectedDatasets"
            display="chip"
            show-clear
            :options="filterableDatasets"
            option-label="dataset_name"
            option-value="id"
            placeholder="Filter by Dataset"
            :loading="experimentsAreLoading"
          />
        </div>
        <div>
          <Button
            label="Run Experiment"
            icon="pi pi-plus"
            @click="createModalOpen = true"
          />
        </div>
      </div>
      <Dialog
        v-model:visible="createModalOpen"
        modal
        header="Create new Dataset"
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
import type { MinimalExperiment, MinimalAgentDto, MinimalDataset } from '@core/sdk/client'

import { useLocalePath } from '#i18n'

const router = useRouter()
const localePath = useLocalePath()
const { t } = useI18n()

const { experiments, experimentsAreLoading } = useExperiments()
const createModalOpen = ref(false)
const runStarted = ref(false)
const runHasErrors = ref(false)
const selectedAgents = useRouteQuery<string[]>('assistants', [])
const selectedDatasets = useRouteQuery<string[]>('datasets', [])

const toExperiment = (experiment: MinimalExperiment) => {
  router.push(localePath(`/admin/evaluation/experiment/${experiment.id}`))
}

const filterableAgents = computed<MinimalAgentDto[]>(() => {
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
