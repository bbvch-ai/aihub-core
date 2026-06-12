<template>
  <div class="flex flex-col gap-2">
    <div class="flex items-center justify-between gap-2">
      <SelectButton
        v-if="navItems"
        :model-value="activeNavItem"
        :options="navItems"
        data-key="key"
        option-label="name"
        size="small"
        @update:model-value="toNavItem"
      />
      <Button
        v-tooltip.top="t('document.delete.button')"
        size="small"
        severity="danger"
        variant="outlined"
        icon="pi pi-trash"
        :label="t('document.delete.button')"
        :loading="isDeleting"
        @click="confirmDelete"
      />
    </div>
    <NuxtPage />
  </div>
</template>

<script setup lang="ts">
import { useConfirm } from 'primevue/useconfirm'
import { useToast } from 'primevue/usetoast'

import type { NavItem } from '@core/types/NavItem'

const router = useRouter()
const route = useRoute()
const tenantPath = useTenantPath()
const { t } = useI18n()
const { tenantId } = useTenant()
const { deleteDocument, isDeleting } = useDeleteDocument()
const confirm = useConfirm()
const toast = useToast()

const subPath = (path: string) => {
  return `/service/knowledge/${route.params.db}/${route.params.namespace}/${route.params.document_id}/${path}`
}

const isActive = (path: string) => {
  return () => {
    const localizedPath = tenantPath(subPath(path))
    return route.path.startsWith(localizedPath)
  }
}

const navItems = computed<NavItem[]>(() => [
  { name: t('knowledge.navigation.document.basic'), key: 'basic', path: subPath('overview'), isActive: isActive('overview') },
  { name: t('knowledge.navigation.document.nodes'), key: 'nodes', path: subPath('nodes'), isActive: isActive('nodes') },
  { name: t('knowledge.navigation.document.summary'), key: 'summary', path: subPath('summary'), isActive: isActive('summary') },
])

const toNavItem = (navItem: NavItem) => {
  router.push(tenantPath(navItem.path))
}

const activeNavItem = computed<NavItem | undefined>(() => {
  return navItems.value?.find(navItem => navItem.isActive())
})

const confirmDelete = () => {
  confirm.require({
    message: t('document.delete.confirmMessage'),
    header: t('document.delete.title'),
    icon: 'pi pi-exclamation-triangle',
    rejectLabel: t('common.actions.cancel'),
    acceptLabel: t('document.delete.button'),
    acceptClass: 'p-button-danger',
    accept: handleDelete,
  })
}

const handleDelete = async () => {
  try {
    await deleteDocument({
      tenantId: tenantId.value!,
      database: route.params.db as string,
      namespace: route.params.namespace as string,
      documentId: route.params.document_id as string,
    })
    toast.add({
      severity: 'success',
      summary: t('document.delete.success'),
      life: 3000,
    })
    router.push(tenantPath(`/service/knowledge/${route.params.db}/${route.params.namespace}`))
  }
  catch (error) {
    toast.add({
      severity: 'error',
      summary: t('document.delete.error'),
      detail: error instanceof Error ? error.message : String(error),
      life: 5000,
    })
  }
}
</script>
