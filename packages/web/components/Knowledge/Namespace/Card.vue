<template>
  <div
    class="flex cursor-pointer flex-col gap-3 rounded-xl border border-surface-200 p-4 hover:bg-surface-100 dark:border-surface-800 hover:dark:bg-surface-800"
    :class="{ 'bg-surface-100 dark:bg-surface-800': isActive }"
  >
    <div class="flex items-center justify-between gap-4">
      <div class="flex items-center justify-start gap-2">
        <div
          class="flex items-center justify-center rounded-full bg-white p-3 dark:bg-surface-900"
        >
          <Icon
            name="mage:book"
            size="1.5em"
          />
        </div>
        <div>
          <h3 class="font-semibold opacity-80">
            {{ displayName }}
          </h3>
          <p
            v-if="namespace.description"
            class="text-sm text-surface-500 dark:text-surface-400"
          >
            {{ namespace.description }}
          </p>
        </div>
      </div>
      <div class="flex items-center gap-2">
        <Button
          v-tooltip.top="t('knowledge.edit_namespace')"
          icon="pi pi-pencil"
          rounded
          text
          size="small"
          severity="secondary"
          @click.stop="handleEditClick"
        />
        <Button
          v-if="!autoSync"
          v-tooltip.top="t('knowledge.upload_documents')"
          icon="pi pi-upload"
          rounded
          text
          size="small"
          severity="secondary"
          @click.stop="handleUploadClick"
        />
        <Badge
          :value="namespace.number_of_documents"
          size="large"
        />
      </div>
    </div>
    <div>
      <div class="text-sm">
        {{ t('knowledge.created_at') }} <span class="font-light">{{ createdAt }}</span>
      </div>
      <div class="text-sm">
        {{ t('knowledge.updated_at') }} <span class="font-light">{{ updatedAt }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { capitalCase } from 'change-case'

import type { NamespaceDto } from '@core/sdk/client'

const props = defineProps<{
  namespace: NamespaceDto
  autoSync?: boolean
}>()

const emit = defineEmits<{
  upload: [namespace: NamespaceDto]
  edit: [namespace: NamespaceDto]
}>()

const route = useRoute()
const { t } = useI18n()

const displayName = computed(() => {
  // Use display_name if available, otherwise fall back to formatted technical name
  return props.namespace.display_name || capitalCase(props.namespace.name)
})

const createdAt = computed(() => {
  return useDateFormat(props.namespace.created_at * 1000, 'DD.MM.YYYY')
})
const updatedAt = computed(() => {
  return useDateFormat(props.namespace.updated_at * 1000, 'DD.MM.YYYY HH:mm')
})

const isActive = computed(() => {
  return route.params.namespace === props.namespace.name
})

const handleUploadClick = (event: Event) => {
  event.stopPropagation()
  emit('upload', props.namespace)
}

const handleEditClick = (event: Event) => {
  event.stopPropagation()
  emit('edit', props.namespace)
}
</script>
