<template>
  <div
    class="flex cursor-pointer flex-col gap-3 rounded-xl border border-surface-200 p-4 hover:bg-surface-100 dark:border-surface-800 hover:dark:bg-surface-800"
    :class="{ 'bg-surface-100 dark:bg-surface-800': isActive }"
    @click="emit('click', agent)"
  >
    <div class="flex items-center justify-between gap-4">
      <div class="flex items-center justify-start gap-2">
        <div
          class="flex items-center justify-center rounded-full bg-white p-3 dark:bg-surface-900"
        >
          <Icon
            :name="agent.agent_config.icon"
            size="1.5em"
          />
        </div>
        <div>
          <h3 class="font-semibold opacity-80">
            {{ agent?.agent_config.name }}
          </h3>
          <p class="text-xs font-light opacity-70">
            {{ agent.agent_class }} / {{ agent.agent_id }}
          </p>
        </div>
      </div>
      <div class="flex items-center gap-2">
        <Tag
          v-if="agent.is_online"
          severity="success"
          :value="t('agent.list.online')"
        />
        <Tag
          v-else
          severity="danger"
          :value="t('agent.list.offline')"
        />
        <Button
          v-if="showDelete"
          icon="pi pi-trash"
          severity="danger"
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
        {{ agent.agent_config.description }}
      </span>
      <div class="pt-2">
        <Tag
          v-if="agent.is_conversational"
          :value="t('agent.can_chat')"
          severity="secondary"
          icon="pi pi-comments"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { AgentDto } from '@core/sdk/client'

const props = withDefaults(defineProps<{
  agent: AgentDto
  showDelete?: boolean
}>(), {
  showDelete: true,
})

const emit = defineEmits<{
  deleted: [agentClass: string, agentId: string]
  click: [agent: AgentDto]
}>()

const route = useRoute()
const { t } = useI18n()
const toast = useToast()
const confirm = useConfirm()
const { deleteAgent, isDeleting } = useDeleteAgent()

const isActive = computed(() => {
  return route.params.agent_id === props.agent.agent_id && route.params.agent_class === props.agent.agent_class
})

function confirmDelete() {
  confirm.require({
    message: t('agent.delete.confirmMessage'),
    header: t('agent.delete.title'),
    icon: 'pi pi-exclamation-triangle',
    rejectLabel: t('agent.create.cancel'),
    acceptLabel: t('agent.delete.button'),
    acceptClass: 'p-button-danger',
    accept: handleDelete,
  })
}

async function handleDelete() {
  try {
    await deleteAgent({
      agentClass: props.agent.agent_class,
      agentId: props.agent.agent_id,
    })

    toast.add({
      severity: 'success',
      summary: t('agent.delete.success'),
      life: 3000,
    })

    emit('deleted', props.agent.agent_class, props.agent.agent_id)
  }
  catch (error) {
    console.error('Failed to delete agent:', error)
    toast.add({
      severity: 'error',
      summary: t('agent.delete.error'),
      detail: error instanceof Error ? error.message : String(error),
      life: 5000,
    })
  }
}
</script>
