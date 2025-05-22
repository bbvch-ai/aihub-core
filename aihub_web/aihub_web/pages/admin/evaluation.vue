<template>
  <StructuralScreen>
    <StructuralColumn
      :title="t('agent.title')"
      :loading="datasetsAreLoading"
    >
      <Button
        label="Show"
        @click="createModalOpen = true"
      />
      <Dialog
        v-model:visible="createModalOpen"
        modal
        header="Edit Profile"
        :style="{ width: '25rem' }"
      >
        <EvaluationDatasetCreate
          @close="createModalOpen = false"
        />
      </Dialog>
      <div
        class="grid grid-cols-2 gap-4 2xl:grid-cols-2"
      >
        <EvaluationDatasetCard
          v-for="dataset in datasets"
          :key="dataset.id"
          :dataset="dataset"
          @click="() => toDataset(dataset)"
        />
      </div>
    </StructuralColumn>
    <NuxtPage />
  </StructuralScreen>
</template>

<script setup lang="ts">
import { useDatasets } from '@core/composables/evaluation/useDatasets'

import type { MinimalDataset } from '@core/sdk/client'

import { useLocalePath } from '#i18n'

const router = useRouter()
const localePath = useLocalePath()
const { t } = useI18n()

const { datasets, datasetsAreLoading } = useDatasets()
const createModalOpen = ref(false)

const toDataset = (dataset: MinimalDataset) => {
  router.push(localePath(`/admin/evaluation/${dataset.id}`))
}
</script>
