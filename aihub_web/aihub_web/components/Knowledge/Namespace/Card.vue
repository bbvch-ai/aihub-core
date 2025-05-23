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
            name="famicons:library-outline"
            size="1.5em"
          />
        </div>
        <h3 class="font-semibold opacity-80">
          {{ name }}
        </h3>
      </div>
      <Badge
        :value="namespace.number_of_documents"
        size="large"
      />
    </div>
    <div>
      <div class="text-sm">
        {{ t('knowledge.created_at') }} <span class="font-light">{{ createdAt }}</span>
      </div>
      <div class="text-sm">
        {{ t('knowledge.updated_at') }} <span class="font-light">{{ updatedAt }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useChangeCase } from '@vueuse/integrations/useChangeCase'

import type { Namespace } from '@core/sdk/client'

const props = defineProps<{
  namespace: Namespace
}>()

const route = useRoute()
const { t } = useI18n()

const name = computed(() => {
  return useChangeCase(props.namespace.name, 'capitalCase')
})

const createdAt = computed(() => {
  return useDateFormat(props.namespace.created_at * 1000, 'DD.MM.YYYY')
})
const updatedAt = computed(() => {
  return useDateFormat(props.namespace.last_updated_at * 1000, 'DD.MM.YYYY HH:mm')
})

const isActive = computed(() => {
  return route.params.namespace === props.namespace.name
})
</script>
