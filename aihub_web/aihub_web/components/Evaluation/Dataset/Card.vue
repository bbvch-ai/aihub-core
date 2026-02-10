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
            name="mage:book"
            size="1.5em"
          />
        </div>
        <h3 class="font-semibold opacity-80">
          {{ dataset.dataset_name }}
        </h3>
      </div>
      <Button
        v-if="langfuseDatasetUrl"
        :label="t('evaluation.langfuse_link')"
        icon="pi pi-external-link"
        icon-pos="right"
        size="small"
        outlined
        as="a"
        :href="langfuseDatasetUrl"
        target="_blank"
        @click.stop
      />
    </div>
    <div>
      <span class="text-xs">
        {{ dataset.description }}
      </span>
    </div>
    <div>
      <div class="text-sm">
        {{ t('evaluation.dataset.created_at') }}
        <span class="font-light">
          {{ useDateFormat(dataset.created_at, 'DD.MM.YYYY') }}
        </span>
      </div>
      <div class="text-sm">
        {{ t('evaluation.dataset.updated_at') }}
        <span class="font-light">
          {{ useDateFormat(dataset.updated_at, 'DD.MM.YYYY') }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { MinimalDataset } from '@core/sdk/client'

const props = defineProps<{
  dataset: MinimalDataset
  langfuseDatasetUrl?: string
}>()

const route = useRoute()
const { t } = useI18n()

const isActive = computed(() => {
  return route.params.dataset_id === props.dataset.id
})
</script>
