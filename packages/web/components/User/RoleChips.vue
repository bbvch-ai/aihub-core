<template>
  <div class="flex flex-wrap items-center gap-2">
    <Chip
      v-for="role in roles"
      :key="role"
      :label="role"
      :removable="!readonly"
      @remove="confirmRevoke(role)"
    />
    <span
      v-if="!roles?.length"
      class="text-sm text-muted-color"
    >
      {{ t('user.role_chips.no_roles') }}
    </span>

    <Button
      v-if="!readonly && assignableRoles.length > 0"
      v-tooltip.top="t('user.role_chips.assign')"
      icon="pi pi-plus"
      text
      rounded
      size="small"
      :aria-label="t('user.role_chips.assign')"
      @click="openAssignMenu($event)"
    />
    <Menu
      ref="assignMenu"
      :model="assignMenuItems"
      :popup="true"
    />
  </div>
</template>

<script setup lang="ts">
import { useConfirm } from 'primevue/useconfirm'

import type { RoleResponse } from '@core/sdk/client'
import type { MenuItem } from 'primevue/menuitem'

const props = defineProps<{
  roles: string[]
  availableRoles: RoleResponse[]
  readonly?: boolean
}>()

const emit = defineEmits<{
  assign: [roleName: string]
  revoke: [roleName: string]
}>()

const { t } = useI18n()
const confirm = useConfirm()

const assignableRoles = computed<RoleResponse[]>(() =>
  (props.availableRoles ?? []).filter(r => !(props.roles ?? []).includes(r.name)),
)

const assignMenu = ref<{ toggle: (event: Event) => void } | null>(null)

const assignMenuItems = computed<MenuItem[]>(() =>
  assignableRoles.value.map(role => ({
    label: role.name,
    icon: 'pi pi-shield',
    command: () => emit('assign', role.name),
  })),
)

const openAssignMenu = (event: Event) => {
  assignMenu.value?.toggle(event)
}

const confirmRevoke = (roleName: string) => {
  confirm.require({
    message: t('user.role_chips.revoke_confirm_message', { role: roleName }),
    header: t('user.role_chips.revoke_confirm_header'),
    icon: 'pi pi-exclamation-triangle',
    rejectProps: { label: t('common.actions.cancel'), severity: 'secondary', outlined: true },
    acceptProps: { label: t('user.role_chips.revoke'), severity: 'danger' },
    accept: () => emit('revoke', roleName),
  })
}
</script>
