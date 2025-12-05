<template>
  <Dialog
    v-model:visible="visible"
    modal
    :header="t('expert.answer_dialog.title')"
    :style="{ width: '50rem' }"
    :breakpoints="{ '1199px': '75vw', '575px': '90vw' }"
  >
    <div
      v-if="question"
      class="flex flex-col gap-4"
    >
      <div class="rounded-lg bg-surface-50 p-4 dark:bg-surface-800">
        <h4 class="mb-2 font-semibold">
          {{ t('expert.answer_dialog.question') }}
        </h4>
        <p class="text-sm">
          {{ question.question }}
        </p>
      </div>

      <div
        v-if="question.context"
        class="rounded-lg bg-surface-50 p-4 dark:bg-surface-800"
      >
        <h4 class="mb-2 font-semibold">
          {{ t('expert.answer_dialog.context') }}
        </h4>
        <p class="max-h-40 overflow-y-auto whitespace-pre-wrap text-sm">
          {{ question.context }}
        </p>
      </div>

      <div>
        <label
          for="answer"
          class="mb-2 block font-semibold"
        >
          {{ t('expert.answer_dialog.your_answer') }}
        </label>
        <Textarea
          id="answer"
          v-model="answer"
          :placeholder="t('expert.answer_dialog.answer_placeholder')"
          rows="6"
          class="w-full"
          auto-resize
        />
      </div>
    </div>

    <template #footer>
      <Button
        :label="t('common.cancel')"
        severity="secondary"
        @click="visible = false"
      />
      <Button
        :label="t('expert.answer_dialog.submit')"
        :loading="isPending"
        :disabled="!answer.trim()"
        @click="submitAnswer"
      />
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { useSubmitExpertAnswer } from '@core/composables/expert/useExpertQuestions'
import { useToast } from 'primevue/usetoast'
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import type { ExpertQuestionDto } from '@core/composables/expert/useExpertQuestions'

const props = defineProps<{
  question: ExpertQuestionDto | null
}>()

const visible = defineModel<boolean>('visible', { default: false })

const emit = defineEmits<{
  submitted: []
}>()

const { t } = useI18n()
const toast = useToast()
const answer = ref('')

const { submitAnswerAsync, isPending } = useSubmitExpertAnswer()

watch(() => props.question, () => {
  answer.value = ''
})

const submitAnswer = async () => {
  if (!props.question || !answer.value.trim())
    return

  try {
    await submitAnswerAsync({
      questionId: props.question.id,
      response: answer.value.trim(),
    })

    toast.add({
      severity: 'success',
      summary: t('expert.answer_dialog.success_title'),
      detail: t('expert.answer_dialog.success_message'),
      life: 3000,
    })

    visible.value = false
    emit('submitted')
  }
  catch {
    toast.add({
      severity: 'error',
      summary: t('expert.answer_dialog.error_title'),
      detail: t('expert.answer_dialog.error_message'),
      life: 5000,
    })
  }
}
</script>
