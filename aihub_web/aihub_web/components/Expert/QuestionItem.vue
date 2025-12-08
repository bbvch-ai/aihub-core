<template>
  <div
    class="flex cursor-pointer flex-col gap-4 border-b border-surface-100 p-4 transition-colors duration-200 hover:bg-surface-50 dark:border-surface-800 dark:hover:bg-surface-800"
    role="listitem"
  >
    <div class="flex items-start justify-between gap-4">
      <div class="min-w-0 grow">
        <div class="mb-2 flex flex-wrap items-center gap-2">
          <Tag
            :value="priorityLabel"
            :severity="prioritySeverity"
            size="small"
          />
          <Tag
            :value="statusLabel"
            :severity="statusSeverity"
            size="small"
          />
          <span class="text-xs font-light opacity-70">
            {{ timeAgoText }}
          </span>
          <span
            v-if="question.expert_group"
            class="text-xs font-light opacity-50"
          >
            {{ t('expert.group') }}: {{ question.expert_group }}
          </span>
        </div>
        <h3 class="mb-2 font-semibold opacity-80">
          {{ question.question }}
        </h3>
        <p
          v-if="question.context"
          class="mb-2 text-xs font-light opacity-70"
        >
          <span class="font-medium">{{ t('expert.context') }}:</span>
          {{ truncatedContext }}
        </p>
        <p class="text-xs font-light opacity-50">
          {{ t('expert.requested_by') }}: {{ question.requesting_user.user_name || question.requesting_user.user_id }}
          ({{ question.requesting_agent.agent_class }})
        </p>
      </div>
      <Button
        v-if="question.status === 'pending'"
        :label="t('expert.answer_button')"
        icon="pi pi-reply"
        size="small"
        @click.stop="$emit('answer', question)"
      />
      <span
        v-else-if="question.responder"
        class="text-xs opacity-70"
      >
        {{ t('expert.answered_by') }}: {{ question.responder.user_name || question.responder.user_id }}
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useTimeAgo } from '@core/composables/useTimeAgo'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import type { ExpertQuestionDto } from '@core/composables/expert/useExpertQuestions'

const props = defineProps<{
  question: ExpertQuestionDto
}>()

defineEmits<{
  answer: [question: ExpertQuestionDto]
}>()

const { t } = useI18n()
const { getTimeAgo } = useTimeAgo()

const timeAgoText = computed(() => getTimeAgo(new Date(props.question.created_at)).text)

const truncatedContext = computed(() => {
  if (!props.question.context)
    return ''
  return props.question.context.length > 200
    ? `${props.question.context.substring(0, 200)}...`
    : props.question.context
})

const priorityLabel = computed(() => {
  const labels: Record<string, string> = {
    low: t('expert.priority.low'),
    normal: t('expert.priority.normal'),
    high: t('expert.priority.high'),
    urgent: t('expert.priority.urgent'),
  }
  return labels[props.question.priority] || props.question.priority
})

const prioritySeverity = computed(() => {
  const severities: Record<string, 'info' | 'success' | 'warn' | 'danger' | undefined> = {
    low: 'info',
    normal: 'success',
    high: 'warn',
    urgent: 'danger',
  }
  return severities[props.question.priority]
})

const statusLabel = computed(() => {
  const labels: Record<string, string> = {
    pending: t('expert.status.pending'),
    answered: t('expert.status.answered'),
    expired: t('expert.status.expired'),
    cancelled: t('expert.status.cancelled'),
  }
  return labels[props.question.status] || props.question.status
})

const statusSeverity = computed(() => {
  const severities: Record<string, 'info' | 'success' | 'warn' | 'danger' | 'secondary' | undefined> = {
    pending: 'warn',
    answered: 'success',
    expired: 'secondary',
    cancelled: 'secondary',
  }
  return severities[props.question.status]
})
</script>
