<template>
  <div>
    <span class="mb-8 block text-surface-500 dark:text-surface-400">
      Create a new experiment with a dataset and an Assistant!
    </span>
    <div class="mb-4 flex flex-col gap-4">
      <div class="flex flex-col">
        <label
          for="name"
          class="font-semibold"
        >
          Name
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
          Description
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
          Dataset
        </label>
        <Select
          v-model="experiment.dataset_id"
          :options="datasets"
          option-label="dataset_name"
          option-value="id"
          placeholder="Select an Dataset"
          :loading="datasetsAreLoading"
        />
      </div>
      <div class="flex flex-col">
        <label
          for="agent"
          class="font-semibold"
        >
          Agent
        </label>
        <Select
          v-model="agent"
          :options="validAgents"
          option-label="agent_config.name"
          placeholder="Select an Assistant"
          :loading="agentsAreLoading"
        />
      </div>
      <div class="flex justify-end gap-2">
        <Button
          type="button"
          label="Cancel"
          severity="secondary"
          @click="close"
        />
        <Button
          type="button"
          label="Save"
          :disabled="!readyToSave"
          @click="save"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { AgentDto, ExperimentCreate } from '@core/sdk/client'

const experiment = ref<ExperimentCreate>({
  agent_class: '',
  agent_id: '',
  dataset_id: '',
  experiment_name: '',
  experiment_description: '',
})
const agent = ref<AgentDto | null>(null)

const { datasets, datasetsAreLoading } = useDatasets()
const { agents, agentsAreLoading } = useAgents()
const { createExperiment } = useCreateExperiment()

const validAgents = computed<AgentDto[]>(() => {
  return agents.value?.filter((agent: AgentDto) => {
    return agent.is_online && agent.is_conversational
  })
})

const readyToSave = computed(() => {
  return agent.value && experiment.value.dataset_id && experiment.value.experiment_name && experiment.value.experiment_description
})

const emit = defineEmits<{
  close: []
  success: []
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
  createExperiment({ experiment: experiment.value })
  emit('success')
}
</script>

<style scoped>

</style>
