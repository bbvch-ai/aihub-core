<template>
  <div
    class="flex cursor-pointer flex-col gap-3 rounded-xl border border-surface-200 p-4 hover:bg-surface-100 dark:border-surface-800 hover:dark:bg-surface-800"
    :class="{ 'bg-surface-100 dark:bg-surface-800': isActive }"
    @click="emit('click', process)"
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
      <div class="flex items-center gap-2">
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
        <Button
          v-if="showDelete"
          icon="pi pi-trash"
          severity="secondary"
          text
          rounded
          size="small"
          :loading="isDeleting"
          @click.stop="confirmDelete"
        />
      </div>
    </div>
    <div>
      <span class="text-xs">
        {{ process.process_config.description }}
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { FullProcessInstanceDtoReadable } from '@core/sdk/client'

const props = withDefaults(defineProps<{
  process: FullProcessInstanceDtoReadable
  showDelete?: boolean
}>(), {
  showDelete: true,
})

const emit = defineEmits<{
  deleted: [processClass: string, processId: string]
  click: [process: FullProcessInstanceDtoReadable]
}>()

const route = useRoute()
const { t } = useI18n()
const toast = useToast()
const confirm = useConfirm()
const { deleteProcessInstance, isDeleting } = useDeleteProcessInstance()

const isActive = computed(() => {
  return route.params.process_id === props.process.process_id && route.params.process_class === props.process.process_class
})

function confirmDelete() {
  confirm.require({
    message: t('process.delete.confirmMessage'),
    header: t('process.delete.title'),
    icon: 'pi pi-exclamation-triangle',
    rejectLabel: t('process.create.cancel'),
    acceptLabel: t('process.delete.button'),
    acceptClass: 'p-button-danger',
    accept: handleDelete,
  })
}

async function handleDelete() {
  try {
    await deleteProcessInstance({
      processClass: props.process.process_class,
      processId: props.process.process_id,
    })

    toast.add({
      severity: 'success',
      summary: t('process.delete.success'),
      life: 3000,
    })

    emit('deleted', props.process.process_class, props.process.process_id)
  }
  catch (error) {
    console.error('Failed to delete process:', error)
    toast.add({
      severity: 'error',
      summary: t('process.delete.error'),
      detail: error instanceof Error ? error.message : String(error),
      life: 5000,
    })
  }
}
</script>
