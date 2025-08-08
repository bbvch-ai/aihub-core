<template>
  <StructuralScreen>
    <StructuralColumn
        :title="t('litellm.title')"
        :loading="modelsAreLoading"
        size="large"
        class="w-1/2 pr-2"
    >
      <div v-if="error" class="mb-4">
        <Message
            severity="error"
            :closable="false"
        >
          {{ t('litellm.error') }}: {{ error }}
        </Message>
      </div>

      <div v-if="!modelsAreLoading && !error && models">
        <ModelsTable
            :models="models"
            @show-details="showModelDetails"
        />
      </div>

      <ModelsDialog
          v-model:visible="modelDialogVisible"
          :model="selectedModel"
      />
    </StructuralColumn>
  </StructuralScreen>
</template>

<script setup lang="ts">
definePageMeta({
  layout: 'default',
})

const {t} = useI18n()

const {models, modelsAreLoading, error} = useModelsList()

const modelDialogVisible = ref(false)
const selectedModel = ref(null)

function showModelDetails(model: any) {
  selectedModel.value = model
  modelDialogVisible.value = true
}
</script>
