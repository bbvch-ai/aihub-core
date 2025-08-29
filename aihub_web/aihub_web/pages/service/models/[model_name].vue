<template>
  <StructuralColumn
    :title="t('models.modelDetails.overview')"
    close-route="/service/models"
    :loading="modelIsLoading"
  >
    <div class="flex flex-col gap-8">
      <Panel class="panel pt-5">
        <div class="grid grid-cols-3 gap-6">
          <div class="flex flex-col items-start gap-2">
            <span class="font-semibold">
              {{ t('models.modelDetails.name') }}
            </span>
            <span class="text-lg font-light">
              {{ model?.model_name || t('models.modelDetails.notSpecified') }}
            </span>
          </div>
          <div class="flex flex-col items-start gap-2">
            <span class="font-semibold">
              {{ t('models.modelDetails.mode') }}
            </span>
            <span class="text-lg font-light capitalize">
              {{ model?.model_info?.mode || t('models.modelDetails.notSpecified') }}
            </span>
          </div>
          <div class="flex flex-col items-start gap-2">
            <span class="font-semibold">
              {{ t('models.modelDetails.maxInputTokens') }}
            </span>
            <span class="text-lg font-light">
              {{
                model?.model_info?.max_input_tokens ? formatNumber(model?.model_info?.max_input_tokens) : t('models.modelDetails.notSpecified')
              }}
            </span>
          </div>
          <div class="flex flex-col items-start gap-2">
            <span class="font-semibold">
              {{ t('models.modelDetails.maxOutputTokens') }}
            </span>
            <span class="text-lg font-light">
              {{
                model?.model_info?.max_output_tokens ? formatNumber(model?.model_info?.max_output_tokens) : t('models.modelDetails.notSpecified')
              }}
            </span>
          </div>
          <div class="flex flex-col items-start gap-2">
            <span class="font-semibold">
              {{ t('models.modelDetails.basicInputCost') }}
            </span>
            <span class="text-lg font-light">
              {{
                isDefined(model?.model_info?.input_cost_per_token) ? `$${model.model_info.input_cost_per_token.toFixed(2)}` : t('models.modelDetails.notSpecified')
              }}
            </span>
          </div>
          <div class="flex flex-col items-start gap-2">
            <span class="font-semibold">
              {{ t('models.modelDetails.basicOutputCost') }}
            </span>
            <span class="text-lg font-light">
              {{
                isDefined(model?.model_info?.output_cost_per_token) ? `$${model.model_info.output_cost_per_token.toFixed(2)}` : t('models.modelDetails.notSpecified')
              }}
            </span>
          </div>
        </div>
      </Panel>

      <ModelDetailsPanel :model="model" />
    </div>
  </StructuralColumn>
</template>

<script setup lang="ts">
import ModelDetailsPanel from '@core/components/Models/ModelDetailsPanel.vue'

const { t } = useI18n()

const { model, modelIsLoading } = useSingleModel()

const formatNumber = (num: number): string => {
  return new Intl.NumberFormat().format(num)
}
</script>
