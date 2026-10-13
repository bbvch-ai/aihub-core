<template>
  <Dialog
    :visible="visible"
    modal
    :header="header"
    class="w-[28rem]"
    @update:visible="emit('update:visible', $event)"
  >
    <form
      class="flex flex-col gap-3"
      @submit.prevent="submit"
    >
      <InputText
        v-model="name"
        autofocus
        :invalid="!isValid && name.length > 0"
      />
      <small
        v-if="!isValid && name.length > 0"
        class="text-red-500"
      >{{ t('userFiles.name.invalid') }}</small>
      <div class="flex justify-end gap-2">
        <Button
          :label="t('userFiles.actions.cancel')"
          severity="secondary"
          text
          @click="emit('update:visible', false)"
        />
        <Button
          type="submit"
          :label="t('userFiles.actions.save')"
          :disabled="!isValid"
        />
      </div>
    </form>
  </Dialog>
</template>

<script setup lang="ts">
const props = defineProps<{ visible: boolean, header: string, initialName?: string }>()
const emit = defineEmits<{ 'update:visible': [boolean], 'submit': [string] }>()
const { t } = useI18n()

const name = ref('')
watch(() => props.visible, (visible) => {
  if (visible) name.value = props.initialName ?? ''
})

const isValid = computed(() => {
  const trimmed = name.value.trim()
  return trimmed.length > 0 && trimmed !== '.' && trimmed !== '..' && !trimmed.includes('/')
})

const submit = () => {
  if (!isValid.value) return
  emit('submit', name.value.trim())
  emit('update:visible', false)
}
</script>
