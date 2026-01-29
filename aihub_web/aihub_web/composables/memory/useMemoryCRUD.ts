import { useToast } from 'primevue/usetoast'
import { useRouter } from 'vue-router'

import type { ComputedRef } from 'vue'

import { useLocalePath } from '#i18n'

export interface UseMemoryCRUDOptions {
  selectedMemory: ComputedRef<{ id: string } | undefined>
  updateMemory: (params: { memoryId: string, data: string }) => Promise<void>
  deleteMemory: (params: { memoryId: string }) => Promise<void>
  closeRoute: string
}

/**
 * Shared composable for memory CRUD operations with toast notifications.
 * Eliminates duplication across user/org detail pages.
 *
 * Provides:
 * - Update handler with success/error toasts (matches MemoryEdit @update signature)
 * - Delete handler with success/error toasts + navigation (matches MemoryEdit @delete signature)
 * - Close handler for navigation back to list (matches MemoryEdit @close signature)
 *
 * @param options - Selected memory ref, CRUD mutation functions, and close route
 * @returns CRUD handlers with toast notifications
 */
export function useMemoryCRUD(options: UseMemoryCRUDOptions) {
  const { t } = useI18n()
  const toast = useToast()
  const router = useRouter()
  const localePath = useLocalePath()

  const handleUpdate = async (data: string) => {
    if (!options.selectedMemory.value) return

    try {
      await options.updateMemory({ memoryId: options.selectedMemory.value.id, data })
      toast.add({
        severity: 'success',
        summary: t('memory.update.success.title'),
        detail: t('memory.update.success.message'),
        life: 3000,
      })
    }
    catch (error) {
      console.error('Failed to update memory:', error)
      toast.add({
        severity: 'error',
        summary: t('memory.update.error.title'),
        detail: t('memory.update.error.message'),
        life: 5000,
      })
    }
  }

  const handleDelete = async () => {
    if (!options.selectedMemory.value) return

    try {
      await options.deleteMemory({ memoryId: options.selectedMemory.value.id })
      toast.add({
        severity: 'success',
        summary: t('memory.delete.success.title'),
        detail: t('memory.delete.success.message'),
        life: 3000,
      })
      // Navigate back to list after successful deletion
      router.push(localePath(options.closeRoute))
    }
    catch (error) {
      console.error('Failed to delete memory:', error)
      toast.add({
        severity: 'error',
        summary: t('memory.delete.error.title'),
        detail: t('memory.delete.error.message'),
        life: 5000,
      })
    }
  }

  const handleClose = () => {
    router.push(localePath(options.closeRoute))
  }

  return {
    handleUpdate,
    handleDelete,
    handleClose,
  }
}
