<template>
  <div
    class="relative flex cursor-pointer flex-col gap-3 rounded-xl border border-surface-200 p-4 hover:bg-surface-100 dark:border-surface-800 hover:dark:bg-surface-800"
    :class="{ 'bg-surface-100 dark:bg-surface-800': isActive }"
  >
    <div>
      <Button
        icon="pi pi-trash"
        severity="contrast"
        variant="text"
        rounded
        aria-label="Trash"
        class="absolute right-2 top-2"
        @click.stop="confirmDelete($event)"
      />
    </div>
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
          {{ role.name }}
        </h3>
      </div>
    </div>
    <div>
      <span class="text-xs">
        {{ role.description }}
      </span>
    </div>
    <div>
      <div class="flex flex-wrap gap-2 text-sm">
        <Badge
          v-for="access_rule in role.access_rules"
          :key="access_rule"
          :value="access_rule"
        />
      </div>
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

const { deleteRole } = useDeleteRole()

const isActive = computed(() => {
  return route.params.role_id === props.role.id
})

const confirmDelete = (event) => {
  confirm.require({
    message: 'Are you sure you want to proceed?',
    header: 'Confirmation',
    icon: 'pi pi-exclamation-triangle',
    position: 'bottom',
    rejectProps: {
      label: 'Cancel',
      severity: 'secondary',
      outlined: true,
    },
    acceptProps: {
      label: 'Delete',
      severity: 'danger',
    },
    accept: async () => {
      await deleteRole({ roleId: props.role.id })
      toast.add({ severity: 'success', summary: 'Confirmed', detail: 'Record deleted', life: 3000 })
    },
    reject: () => {
    },
  })
}
</script>

<style scoped>

</style>
