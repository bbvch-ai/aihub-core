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
            :langfuse-dataset-url="dataset.langfuse_url"
            @click="() => toDataset(dataset)"
          />
        </div>
      </div>
    </StructuralColumn>

    <NuxtPage />
  </StructuralScreen>
</template>

<script setup lang="ts">
const router = useRouter()
const tenantPath = useTenantPath()
const { t } = useI18n()

const { datasets, datasetsAreLoading } = useDatasets()
const createModalOpen = ref(false)

const toDataset = (dataset: { id: string }) => {
  router.push(tenantPath(`/service/datasets/${dataset.id}`))
}
</script>
