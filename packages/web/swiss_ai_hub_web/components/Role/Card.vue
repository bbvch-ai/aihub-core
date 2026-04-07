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
            class="border border-gray-400/30"
          />
        </div>
      </div>
      <Button
        icon="pi pi-trash"
        severity="contrast"
        variant="text"
        rounded
        aria-label="Trash"
        @click.stop="confirmDelete($event)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { useDeleteRole } from '@core/composables/role/useDeleteRole'

import type { RoleResponse } from '@core/sdk/client'

const props = defineProps<{
  role: RoleResponse
}>()

const route = useRoute()
const confirm = useConfirm()
const toast = useToast()
const { t } = useI18n()
const router = useRouter()
const tenantPath = useTenantPath()

const { deleteRole } = useDeleteRole()

const isActive = computed(() => {
  return route.params.role_id === props.role.id
})

const confirmDelete = () => {
  confirm.require({
    message: t('role.remove_dialog.explanation'),
    header: t('role.remove_dialog.confirm'),
    icon: 'pi pi-exclamation-triangle',
    position: 'bottom',
    rejectProps: {
      label: t('role.remove_dialog.cancel'),
      severity: 'secondary',
      outlined: true,
    },
    acceptProps: {
      label: t('role.remove_dialog.proceed'),
      severity: 'danger',
    },
    accept: async () => {
      await router.push(tenantPath('/service/roles'))
      await deleteRole({ roleId: props.role.id })
      toast.add({ severity: 'success', summary: t('role.role_deleted.summary'), detail: t('role.role_deleted.detail'), life: 3000 })
    },
    reject: () => {
    },
  })
}
</script>

<style scoped>

</style>
