<template>
  <StructuralScreen>
    <StructuralColumn
      :title="t('process.title')"
      :loading="processesAreLoading"
    >
      <div
        class="grid grid-cols-2 gap-4 2xl:grid-cols-2"
      >
        <!-- <ProcessCard -->
        <div
          v-for="process in processes"
          :key="process.process_id"
          :process="process"
          @click="() => toProcess(process)"
        />
      </div>
    </StructuralColumn>

    <NuxtPage />
  </StructuralScreen>
</template>

<script setup lang="ts">
import type { ProcessDto } from '@core/sdk/client'

import { useLocalePath } from '#i18n'

const router = useRouter()
const localePath = useLocalePath()
const { t } = useI18n()

const { processes, processesAreLoading } = useProcesses()

const toProcess = (process: ProcessDto) => {
  router.push(localePath(`/service/processes/process-${process.process_id}-${process.process_class}/overview`))
}
</script>
