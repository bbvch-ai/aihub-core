<template>
  <StructuralColumn
    :title="processInstance?.process_config.name"
    close-route="/service/processes"
    :loading="processInstanceIsLoading"
    size="large"
  >
    <div class="flex flex-col gap-12">
      <ProcessStarts
        :human-inputs="startInputs"
      />
    </div>
  </StructuralColumn>
</template>

<script setup lang="ts">
import type { HumanInSpecsReadable } from '@core/sdk/client'

const { processInstance, processInstanceIsLoading } = useProcessInstance()

const startInputs = computed<HumanInSpecsReadable[]>(() => {
  return processInstance.value?.human_inputs?.filter((input: HumanInSpecsReadable) => {
    return input.is_process_start
  })
})
</script>
