<template>
  <div
    class="flex cursor-pointer flex-col gap-3 rounded-xl border border-surface-200 p-4 hover:bg-surface-100 dark:border-surface-800 hover:dark:bg-surface-800"
    :class="{ 'bg-surface-100 dark:bg-surface-800': isActive }"
  >
    <div class="flex items-center justify-between gap-4">
      <div class="flex items-center justify-start gap-2">
        <div
          class="flex items-center justify-center rounded-full bg-white p-3 dark:bg-surface-900"
        >
          <Icon
            :name="experiment.agent.agent_config.icon"
            size="1.5em"
          />
        </div>
        <div>
          <h3 class="font-semibold opacity-80">
            {{ experiment.name }}
          </h3>
          <p class="text-xs font-light opacity-70">
            {{ experiment.agent?.agent_config.name }}
          </p>
        </div>
      </div>
      <div class="flex gap-2">
        <Tag
          severity="secondary"
          :value="t(`languages.${experiment.locale}`)"
        />
        <Tag
          severity="contrast"
          :value="experiment.dataset.dataset_name"
        />
      </div>
    </div>
    <div>
      <span class="text-xs">
        {{ experiment.description }}
      </span>
    </div>
    <div>
      <div class="text-sm">
        {{ t('evaluation.experiment.created_at') }}
        <span class="font-light">
          {{ useDateFormat(experiment.created_at, 'DD.MM.YYYY') }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { MinimalExperiment } from '@core/sdk/client'

const props = defineProps<{
  experiment: MinimalExperiment
}>()

const route = useRoute()
const { t } = useI18n()

const isActive = computed(() => {
  return route.params.experiment_id === props.experiment.id
})
</script>
