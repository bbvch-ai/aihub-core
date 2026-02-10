<template>
  <StructuralScreen>
    <StructuralColumn
      :title="t('evaluation.dataset.title')"
      :loading="datasetsAreLoading"
    >
      <div class="flex flex-col gap-2">
        <div class="flex w-full justify-end">
          <Button
            :label="t('evaluation.dataset.create_new')"
            icon="pi pi-plus"
            @click="createModalOpen = true"
          />
          <Dialog
            v-model:visible="createModalOpen"
            modal
            :header="t('evaluation.dataset.create_new')"
          >
            <EvaluationDatasetCreate
              @close="createModalOpen = false"
            />
          </Dialog>
        </div>
        <div
          class="grid grid-cols-2 gap-4 xl:grid-cols-2"
        >
          <EvaluationDatasetCard
            v-for="dataset in datasets"
            :key="dataset.id"
            :dataset="dataset"
            :langfuse-dataset-url="langfuseDatasetUrl(dataset)"
            @click="() => toDataset(dataset)"
          />
        </div>
      </div>
    </StructuralColumn>

    <NuxtPage />
  </StructuralScreen>
</template>

<script setup lang="ts">
import type { MinimalDataset } from '@core/sdk/client'

import { useLocalePath } from '#i18n'

const router = useRouter()
const localePath = useLocalePath()
const { t } = useI18n()

const langfuseConfig = useRuntimeConfig().public.langfuse

const { datasets, datasetsAreLoading } = useDatasets()
const createModalOpen = ref(false)

const langfuseDatasetUrl = (dataset: MinimalDataset) =>
  `${langfuseConfig.url}/project/${langfuseConfig.projectId}/datasets/${dataset.id}`

const toDataset = (dataset: MinimalDataset) => {
  router.push(localePath(`/service/datasets/${dataset.id}`))
}
</script>
