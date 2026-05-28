<template>
  <div
    class="flex cursor-pointer flex-col gap-3 rounded-xl border border-surface-200 p-4 hover:bg-surface-100 dark:border-surface-800 hover:dark:bg-surface-800"
    :class="{ 'bg-surface-100 dark:bg-surface-800': isActive }"
  >
    <div class="flex items-start gap-3">
      <div class="flex flex-1 flex-col gap-3">
        <div class="flex items-center gap-2">
          <div
            class="flex items-center justify-center rounded-full bg-white p-3 dark:bg-surface-900"
          >
            <Icon
              name="mage:book"
              size="1.5em"
            />
          </div>
          <h3 class="font-semibold opacity-80">
            {{ role.name }}
          </h3>
        </div>
        <span
          v-if="role.description"
          class="text-xs"
        >
          {{ role.description }}
        </span>
        <div class="flex flex-wrap gap-2 text-sm">
          <Badge
            v-for="access_rule in role.access_rules"
            :key="access_rule"
            :value="access_rule"
            severity="secondary"
            class="border border-surface-200 dark:border-surface-700"
          />
        </div>
      </div>
      <Button
        icon="pi pi-trash"
        severity="contrast"
        variant="text"
        rounded
        :aria-label="t('common.actions.delete')"
        @click.stop="emit('delete', props.role)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import type { RoleResponse } from '@core/sdk/client'

const props = defineProps<{
  role: RoleResponse
}>()

const emit = defineEmits<{
  delete: [role: RoleResponse]
}>()

const { t } = useI18n()
const route = useRoute()

const isActive = computed(() => {
  return route.params.role_id === props.role.id
})
</script>
