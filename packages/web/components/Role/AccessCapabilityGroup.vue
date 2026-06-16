<template>
  <div class="flex flex-col">
    <!-- Service header: icon + name + hairline rule -->
    <div
      v-if="depth === 0"
      class="flex items-center gap-2.5 border-b border-surface-200 pb-2.5 dark:border-surface-800"
    >
      <Icon
        v-if="group.icon"
        :name="group.icon"
        size="1.4em"
        class="text-surface-500 dark:text-surface-400"
      />
      <span class="text-lg font-bold">{{ group.label }}</span>
    </div>

    <!-- Class subtitle -->
    <div
      v-else-if="depth === 1"
      class="flex items-center gap-2"
    >
      <Icon
        v-if="group.icon"
        :name="group.icon"
        size="1.2em"
        class="text-surface-500 dark:text-surface-400"
      />
      <span class="text-base font-semibold text-surface-700 dark:text-surface-200">
        {{ group.label }}
      </span>
    </div>

    <!-- Instance subtitle -->
    <div
      v-else
      class="flex items-center gap-2 text-sm font-medium text-surface-600 dark:text-surface-300"
    >
      <span class="size-1.5 rounded-full bg-surface-300 dark:bg-surface-600" />
      {{ group.label }}
    </div>

    <!-- Capabilities -->
    <div
      class="flex flex-col gap-1"
      :class="depth === 0 ? 'mt-3' : 'mt-2'"
    >
      <label
        v-for="cap in group.capabilities"
        :key="cap.key"
        class="group/cap flex items-start gap-3 rounded-md py-1 pr-1"
        :class="readonly || !cap.toggleable || cap.locked ? 'cursor-default' : 'cursor-pointer'"
      >
        <Checkbox
          :model-value="cap.granted"
          binary
          :disabled="readonly || !cap.toggleable || cap.locked"
          size="small"
          class="mt-0.5"
          @update:model-value="(value) => onToggle(cap, value)"
        />
        <span class="flex min-w-0 flex-1 flex-col">
          <span class="flex items-center gap-1.5 text-sm leading-tight">
            {{ cap.label }}
            <template v-if="!readonly">
              <i
                v-if="cap.locked"
                v-tooltip.top="t('role.capability_locked')"
                class="pi pi-lock text-[10px] text-surface-400"
              />
              <i
                v-else-if="!cap.toggleable"
                v-tooltip.top="t('role.capability_readonly')"
                class="pi pi-eye text-[10px] text-surface-400"
              />
            </template>
          </span>
          <span class="mt-0.5 text-xs leading-snug text-surface-500 dark:text-surface-400">{{ cap.description }}</span>
        </span>
        <code
          v-if="cap.rule"
          class="mt-0.5 shrink-0 font-mono text-[11px] text-surface-300 transition-colors group-hover/cap:text-surface-500 dark:text-surface-600 dark:group-hover/cap:text-surface-400"
        >{{ cap.rule }}</code>
      </label>
    </div>

    <!-- Nested groups (classes, then instances) -->
    <div
      v-if="group.groups.length"
      class="mt-4 flex flex-col gap-6"
      :class="depth === 0 ? 'pl-1' : 'pl-4'"
    >
      <AccessCapabilityGroup
        v-for="sub in group.groups"
        :key="sub.key"
        :group="sub"
        :depth="depth + 1"
        :readonly="readonly"
        @add="(rule) => emit('add', rule)"
        @remove="(rule) => emit('remove', rule)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import type { Capability, CapabilityGroup } from '@core/sdk/client'

const { t } = useI18n()

const props = withDefaults(defineProps<{
  group: CapabilityGroup
  depth?: number
  readonly?: boolean
}>(), {
  depth: 0,
  readonly: false,
})

const emit = defineEmits<{
  add: [rule: string]
  remove: [rule: string]
}>()

const onToggle = (cap: Capability, value: boolean) => {
  if (props.readonly || !cap.rule) return
  emit(value ? 'add' : 'remove', cap.rule)
}
</script>
