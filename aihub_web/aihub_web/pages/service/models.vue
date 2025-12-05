<template>
  <StructuralScreen>
    <StructuralColumn
      :title="t('models.title')"
      :loading="modelsAreLoading"
    >
      <div
        v-if="error"
        class="mb-4"
      >
        <Message
          severity="error"
          :closable="false"
        >
          {{ t('models.error') }}: {{ error }}
        </Message>
      </div>

      <div class="flex flex-col gap-12">
        <div
          v-for="modelType in modelTypes"
          :key="modelType.name"
        >
          <div
            class="pb-2 pl-2 text-sm font-medium"
          >
            {{ useChangeCase(modelType.name, 'capitalCase') }}
          </div>
          <div
            class="grid grid-cols-2 gap-4 2xl:grid-cols-2"
          >
            <ModelsNamespaceCard
              v-for="model in modelType.models"
              :key="model.model_name"
              :model="model"
              @click="() => showModelDetails(model)"
            />
          </div>
        </div>
      </div>
    </StructuralColumn>

    <NuxtPage />
  </StructuralScreen>
</template>

<script setup lang="ts">
import { useChangeCase } from '@vueuse/integrations/useChangeCase'

import type { ModelDtoReadable } from '@core/sdk/client'

import { useLocalePath } from '#i18n'

const router = useRouter()
const localePath = useLocalePath()
const { t } = useI18n()

const { modelTypes, modelsAreLoading, error } = useModelsList()

function showModelDetails(model: ModelDtoReadable) {
  router.push(localePath(`/service/models/${encodeURIComponent(model.model_name)}`))
}
</script>
