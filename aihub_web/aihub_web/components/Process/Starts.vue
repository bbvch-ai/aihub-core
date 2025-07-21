<template>
  <div>
    <ProcessForm
      v-for="(humanInput, index) in humanInputs"
      :key="index"
      class="w-1/2"
      :title="humanInput.name"
      :description="humanInput.description"
      :form="humanInput.form"
      @submit="submitForm($event, humanInput)"
    />
  </div>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'

import type { HumanInDtoReadable } from '@core/sdk/client'

defineProps<{
  humanInputs: HumanInDtoReadable[]
}>()

const route = useRoute()
const { sendProcessStartForm } = useSendProcessStartForm()

const submitForm = async (form: Record<string, unknown>, humanInput: HumanInDtoReadable) => {
  console.log(form)
  await sendProcessStartForm({
    processClass: route.params.process_class as string,
    processId: route.params.process_id as string,
    submissionRoute: humanInput.route,
    submissionMethod: humanInput.method,
    data: form,
  })
}
</script>

<style scoped>

</style>
