<template>
  <Dialog
    :visible="visible"
    modal
    :header="t('userFiles.move.header', { name: entry?.name ?? '' })"
    class="w-[28rem]"
    @update:visible="emit('update:visible', $event)"
  >
    <div class="flex flex-col gap-3">
      <Listbox
        v-model="target"
        :options="targets"
        option-label="label"
        option-value="folder"
        class="w-full"
        :empty-message="t('userFiles.move.noTargets')"
      >
        <template #option="{ option }">
          <div class="flex items-center gap-2">
            <Icon
              :name="option.up ? 'mage:arrow-up' : 'mage:folder'"
              class="text-surface-500"
            />
            <span>{{ option.label }}</span>
          </div>
        </template>
      </Listbox>
      <div class="flex justify-end gap-2">
        <Button
          :label="t('userFiles.actions.cancel')"
          severity="secondary"
          text
          @click="emit('update:visible', false)"
        />
        <Button
          :label="t('userFiles.actions.move')"
          :disabled="target == null"
          @click="submit"
        />
      </div>
    </div>
  </Dialog>
</template>

<script setup lang="ts">
import type { FileEntryDto } from '@core/sdk/client'

const props = defineProps<{
  visible: boolean
  entry?: FileEntryDto
  folder: string
  folders: FileEntryDto[]
  parentLabel: string
}>()
const emit = defineEmits<{ 'update:visible': [boolean], 'submit': [string] }>()
const { t } = useI18n()

const target = ref<string | null>(null)
watch(() => props.visible, (visible) => {
  if (visible) target.value = null
})

const parentOf = (path: string) => (path.includes('/') ? path.slice(0, path.lastIndexOf('/')) : '.')

const targets = computed(() => [
  ...(props.folder === '.' ? [] : [{ label: props.parentLabel, folder: parentOf(props.folder), up: true }]),
  ...props.folders
    .filter(folder => folder.path !== props.entry?.path)
    .map(folder => ({ label: folder.conversation_title ?? folder.name, folder: folder.path, up: false })),
])

const submit = () => {
  if (target.value == null) return
  emit('submit', target.value)
  emit('update:visible', false)
}
</script>
