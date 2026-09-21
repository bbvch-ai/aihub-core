<template>
  <Dialog
    :visible="visible"
    modal
    :header="title"
    :style="{ width: '32rem' }"
    :closable="!isDeleting"
    @update:visible="emit('update:visible', $event)"
  >
    <div class="flex flex-col gap-4">
      <Message
        severity="warn"
        :closable="false"
      >
        {{ warning }}
      </Message>

      <div class="flex flex-col gap-2">
        <label
          for="delete-confirm-input"
          class="text-sm font-medium"
        >
          {{ t('knowledge.delete.confirm_label', { name: expectedName }) }}
        </label>
        <!-- Deliberately no placeholder: the label already names what to type, and putting it in the
             field too turns a deliberate confirmation into copying the answer out of the box. -->
        <InputText
          id="delete-confirm-input"
          v-model="typedName"
          autocomplete="off"
          :disabled="isDeleting"
          @keyup.enter="confirmIfMatch"
        />
      </div>
    </div>

    <template #footer>
      <div class="flex justify-end gap-2">
        <Button
          :label="t('knowledge.actions.cancel')"
          severity="secondary"
          outlined
          :disabled="isDeleting"
          @click="emit('update:visible', false)"
        />
        <Button
          :label="t('knowledge.delete.actions.delete')"
          severity="danger"
          :disabled="!nameMatches"
          :loading="isDeleting"
          @click="emit('confirm')"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
const props = defineProps<{
  visible: boolean
  title: string
  warning: string
  expectedName: string
  isDeleting?: boolean
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
  'confirm': []
}>()

const { t } = useI18n()

const typedName = ref('')

const nameMatches = computed(() => typedName.value.trim() === props.expectedName)

const confirmIfMatch = () => {
  if (nameMatches.value && !props.isDeleting) emit('confirm')
}

// Reset the typed name whenever the dialog opens for a different target, so a previous confirmation
// can never carry over and pre-satisfy the guard.
watch(() => props.visible, (isVisible) => {
  if (isVisible) typedName.value = ''
})
</script>
