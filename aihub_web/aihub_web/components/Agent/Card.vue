<template>
  <div class="flex cursor-pointer flex-col gap-3 rounded-xl border border-surface-200 p-4 hover:bg-surface-100 dark:border-surface-800 hover:dark:bg-surface-800">
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
      <div>
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
import type { AgentDto, MinimalAgentDto } from '@core/sdk/client'

defineProps<{
  agent: AgentDto
}>()

const { t } = useI18n()
</script>

<style scoped>

</style>
