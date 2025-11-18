<template>
  <StructuralColumn
    :title="process?.process_config.name"
    close-route="/service/processes"
    :loading="processIsLoading"
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
import type { HumanInDtoReadable } from '@core/sdk/client'

const { process, processIsLoading } = useProcess()

const startInputs = computed<HumanInDtoReadable[]>(() => {
  return process.value?.human_inputs?.filter((input: HumanInDtoReadable) => {
    return input.is_process_start
  })
})
</script>
