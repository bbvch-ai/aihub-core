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
import type { HumanInDto } from '@core/sdk/client'

const { process, processIsLoading } = useProcess()
const { t } = useI18n()

const startInputs = computed<HumanInDto[]>(() => {
  return process.value?.human_inputs?.filter((input: HumanInDto) => {
    return input.is_process_start
  })
})
</script>
