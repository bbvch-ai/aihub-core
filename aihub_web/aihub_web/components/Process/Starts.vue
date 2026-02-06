<template>
  <div>
    <ProcessForm
      v-for="(humanInput, index) in humanInputs"
      :key="index"
      class="w-1/2"
      :title="resolveLocale(humanInput.name)"
      :description="resolveLocale(humanInput.description)"
      :form="humanInput.form"
      @submit="submitForm($event, humanInput)"
    />
  </div>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'

import type { HumanInSpecsReadable, LocaleString } from '@core/sdk/client'

defineProps<{
  humanInputs: HumanInSpecsReadable[]
}>()

const route = useRoute()
const { locale } = useI18n()
const { sendProcessStartForm } = useSendProcessStartForm()

const resolveLocale = (localeString: LocaleString): string => {
  const key = locale.value as keyof LocaleString
  return localeString?.[key] ?? localeString?.en ?? localeString?.de ?? ''
}

const submitForm = async (form: Record<string, unknown>, humanInput: HumanInSpecsReadable) => {
  await sendProcessStartForm({
    processClass: route.params.process_class as string,
    processId: route.params.process_id as string,
    submissionRoute: humanInput.route,
    submissionMethod: humanInput.method,
    data: form,
  })
}
</script>
