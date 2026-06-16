<template>
  <div class="flex flex-col gap-1 rounded-lg border border-surface-200 p-6 dark:border-surface-700">
    <div class="flex items-center gap-2">
      <span class="text-xl font-bold">
        {{ readonly ? t('role.capabilities_readonly_title') : t('role.capabilities_title') }}
      </span>
      <ProgressSpinner
        v-if="capabilitiesAreLoading"
        style="width: 1rem; height: 1rem"
        stroke-width="6"
      />
    </div>
    <p class="text-xs text-surface-500 dark:text-surface-400">
      {{ readonly ? t('role.capabilities_readonly_subtitle') : t('role.capabilities_subtitle') }}
    </p>

    <div class="mt-5 flex flex-col gap-10">
      <AccessCapabilityGroup
        v-for="group in capabilities?.groups ?? []"
        :key="group.key"
        :group="group"
        :depth="0"
        :readonly="readonly"
        @add="(rule) => emit('add', rule)"
        @remove="(rule) => emit('remove', rule)"
      />
    </div>
    <p
      v-if="!capabilitiesAreLoading && !(capabilities?.groups?.length)"
      class="text-sm italic text-surface-500 dark:text-surface-400"
    >
      {{ t('role.capabilities_empty') }}
    </p>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import AccessCapabilityGroup from './AccessCapabilityGroup.vue'

import { useAccessCapabilities } from '@/composables/access/useAccessCapabilities'

const { t } = useI18n()

const props = withDefaults(defineProps<{
  rules: string[]
  restrictToTenant?: boolean
  readonly?: boolean
}>(), {
  restrictToTenant: true,
  readonly: false,
})

const emit = defineEmits<{
  add: [rule: string]
  remove: [rule: string]
}>()

const { capabilities, capabilitiesAreLoading } = useAccessCapabilities(
  () => props.rules,
  () => props.restrictToTenant,
)
</script>
