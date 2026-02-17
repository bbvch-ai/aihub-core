<template>
  <div>
    <span class="mb-8 block text-surface-500 dark:text-surface-400">
      {{ t('evaluation.experiment.create_description') }}
    </span>
    <div class="mb-4 flex flex-col gap-4">
      <div class="flex flex-col">
        <label
          for="name"
          class="font-semibold"
        >
          {{ t('evaluation.experiment.name') }}
        </label>
        <InputText
          id="name"
          v-model="experiment.experiment_name"
          class="flex-auto"
          autocomplete="off"
        />
      </div>
      <div class="flex flex-col">
        <label
          for="description"
          class="w-24 font-semibold"
        >
          {{ t('evaluation.experiment.description') }}
        </label>
        <Textarea
          id="description"
          v-model="experiment.experiment_description"
          class="flex-auto"
          autocomplete="off"
        />
      </div>
      <div class="flex flex-col">
        <label
          for="dataset"
          class="w-24 font-semibold"
        >
          {{ t('evaluation.experiment.dataset') }}
        </label>
        <Select
          v-model="experiment.dataset_id"
          :options="datasets"
          option-label="dataset_name"
          option-value="id"
          :placeholder="t('evaluation.experiment.select_dataset')"
          :loading="datasetsAreLoading"
        />
      </div>
      <div class="flex flex-col">
        <label
          for="agent"
          class="font-semibold"
        >
          {{ t('evaluation.experiment.agent') }}
        </label>
        <Select
          v-model="agent"
          :options="validAgents"
          option-label="agent_config.name"
          :placeholder="t('evaluation.experiment.select_assistant')"
          :loading="agentInstancesAreLoading"
        />
      </div>
      <div class="flex justify-end gap-2">
        <Button
          type="button"
          :label="t('evaluation.experiment.cancel')"
          severity="secondary"
          @click="close"
        />
        <Button
          type="button"
          :label="t('evaluation.experiment.save')"
          :disabled="!readyToSave"
          @click="save"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import type { ExperimentCreate, FullAgentInstanceDto } from '@core/sdk/client'

const { t } = useI18n()

const experiment = ref<ExperimentCreate>({
  agent_class: '',
  agent_id: '',
  dataset_id: '',
  experiment_name: '',
  experiment_description: '',
})
const agent = ref<FullAgentInstanceDto | null>(null)

const { datasets, datasetsAreLoading } = useDatasets()
const { agentInstances, agentInstancesAreLoading } = useAgentInstances()
const { createExperiment } = useCreateExperiment()

const validAgents = computed<FullAgentInstanceDto[]>(() => {
  return agentInstances.value?.filter((agent: FullAgentInstanceDto) => {
    return agent.is_online && agent.is_conversational
  })
})

const readyToSave = computed(() => {
  return agent.value && experiment.value.dataset_id && experiment.value.experiment_name && experiment.value.experiment_description
})

const emit = defineEmits<{
  close: []
  success: [Promise<void>]
}>()

const close = () => {
  emit('close')
}
const save = () => {
  if (!agent.value) {
    return
  }
  experiment.value.agent_class = agent.value.agent_class
  experiment.value.agent_id = agent.value.agent_id
  const promise = createExperiment({ experiment: experiment.value })
  emit('success', promise)
}
</script>
