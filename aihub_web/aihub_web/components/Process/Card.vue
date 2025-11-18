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
            :name="process.process_config.icon"
            size="1.5em"
          />
        </div>
        <div>
          <h3 class="font-semibold opacity-80">
            {{ process?.process_config.name }}
          </h3>
          <p class="text-xs font-light opacity-70">
            {{ process.process_class }} / {{ process.process_id }}
          </p>
        </div>
      </div>
      <div>
        <Tag
          v-if="process.is_online"
          severity="success"
          :value="t('process.list.online')"
        />
        <Tag
          v-else
          severity="danger"
          :value="t('process.list.offline')"
        />
      </div>
    </div>
    <div>
      <span class="text-xs">
        {{ process.process_config.description }}
      </span>
      <div class="pt-2">
        <Tag
          v-if="process.is_conversational"
          :value="t('process.can_chat')"
          severity="secondary"
          icon="pi pi-comments"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { ProcessDto } from '@core/sdk/client'

const props = defineProps<{
  process: ProcessDto
}>()

const route = useRoute()
const { t } = useI18n()

const isActive = computed(() => {
  return route.params.process_id === props.process.process_id && route.params.process_class === props.process.process_class
})
</script>
