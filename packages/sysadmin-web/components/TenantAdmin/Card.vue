<!-- SPDX-License-Identifier: LicenseRef-Proprietary -->
<template>
  <div
    class="flex flex-col gap-3 rounded-xl border border-surface-200 p-4 dark:border-surface-800"
    :class="[
      isOrphaned
        ? 'cursor-not-allowed opacity-60'
        : 'cursor-pointer hover:bg-surface-100 hover:dark:bg-surface-800',
      { 'bg-surface-100 dark:bg-surface-800': isActive && !isOrphaned },
    ]"
  >
    <div class="flex items-start gap-3">
      <div class="flex flex-1 flex-col gap-3">
        <div class="flex flex-wrap items-center gap-2">
          <div class="flex items-center justify-center rounded-full bg-white p-3 dark:bg-surface-900">
            <Icon
              name="mage:building-b"
              size="1.5em"
            />
          </div>
          <h3 class="font-semibold opacity-80">
            {{ tenant.name }}
          </h3>
          <Tag
            v-if="isOrphaned"
            v-tooltip.top="{ value: t('tenant_admin.state.orphaned_tooltip') }"
            :value="t('tenant_admin.state.orphaned_label')"
            severity="warn"
            icon="pi pi-exclamation-triangle"
          />
        </div>
        <span class="text-xs text-surface-500 dark:text-surface-500">
          {{ tenant.id }}
        </span>
        <span
          v-if="tenant.description"
          class="text-xs"
        >
          {{ tenant.description }}
        </span>
        <div class="flex flex-wrap gap-2 text-sm">
          <Badge
            v-for="access_rule in tenant.access_rules"
            :key="access_rule"
            :value="access_rule"
            severity="secondary"
            class="border border-surface-200 dark:border-surface-700"
          />
        </div>
      </div>
      <Button
        v-if="canDelete"
        icon="pi pi-trash"
        severity="contrast"
        variant="text"
        rounded
        aria-label="Delete"
        @click.stop="confirmDelete"
      />
      <Button
        v-else
        v-tooltip.left="{ value: t('tenant_admin.delete_dialog.last_tenant_blocked') }"
        icon="pi pi-trash"
        severity="contrast"
        variant="text"
        rounded
        disabled
        aria-label="Delete (disabled)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import type { TenantResponse } from '~/sdk/client'

const props = withDefaults(
  defineProps<{
    tenant: TenantResponse
    canDelete?: boolean
  }>(),
  {
    canDelete: true,
  },
)

const route = useRoute()
const confirm = useConfirm()
const toast = useToast()
const { t } = useI18n()
const router = useRouter()
const localePath = useLocalePath()

const { deleteTenantMetadata } = useDeleteTenantMetadata()

const isActive = computed(() => {
  return route.params.tenant_id === props.tenant.id
})

const isOrphaned = computed(() => props.tenant.state === 'orphaned')

const confirmDelete = () => {
  confirm.require({
    message: t('tenant_admin.delete_dialog.explanation', { name: props.tenant.name }),
    header: t('tenant_admin.delete_dialog.confirm'),
    icon: 'pi pi-exclamation-triangle',
    position: 'bottom',
    rejectProps: {
      label: t('tenant_admin.cancel'),
      severity: 'secondary',
      outlined: true,
    },
    acceptProps: {
      label: t('tenant_admin.delete_dialog.proceed'),
      severity: 'danger',
    },
    accept: async () => {
      if (isActive.value) {
        await router.push(localePath('/sysadmin/tenants'))
      }
      await deleteTenantMetadata({ tenantId: props.tenant.id })
      toast.add({ severity: 'success', summary: t('tenant_admin.tenant_deleted.summary'), detail: t('tenant_admin.tenant_deleted.detail'), life: 3000 })
    },
  })
}
</script>
