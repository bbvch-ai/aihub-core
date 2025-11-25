<template>
  <Panel
    :header="title"
    toggleable
  >
    <p class="text-xs dark:text-surface-500">
      {{ description }}
    </p>
    <div class="content pt-6">
      <div class="w-full">
        <FormKit
          id="form"
          v-model="data"
          type="form"
          :submit-attrs="{
            inputClass: 'p-button p-component w-full',
          }"
          :config="{
            validationVisibility: 'blur',
          }"
          @submit="submitHandler"
        >
          <FormKitSchema
            :schema="schema"
            :data="data"
          />
        </FormKit>
      </div>
    </div>
    <pre>{{ data }}</pre>
  </Panel>
</template>

<script setup lang="ts">
import type { FormkitElement } from '@core/sdk/client'
import type { FormKitSchemaNode, FormKitSchemaDefinition } from '@formkit/core'

const props = defineProps<{
  title: string
  description: string
  form: FormkitElement[]
  initialData?: Record<string, unknown>
}>()

// Initialize form data with initialData prop
// Start with initialData if available, otherwise empty object
const data = ref<Record<string, unknown>>(props.initialData || {})

// Watch for changes in initialData and update form data
// Use deep: true to ensure nested changes are detected
watch(() => props.initialData, (newData) => {
  if (newData && Object.keys(newData).length > 0) {
    // Merge with existing data to preserve any user changes
    data.value = { ...data.value, ...newData }
  }
}, { deep: true })

const emit = defineEmits<{
  submit: [Record<string, unknown>]
}>()

const schema = computed<FormKitSchemaDefinition>(() => {
  const pattern = new RegExp(
    Object.keys(data.value)
      .map(key => `\\$${key}`)
      .join('|'),
    'g',
  )
  return props.form.map((formElement: FormkitElement) => {
    const formkitNode = {
      ...formElement,
      $formkit: (formElement as Record<string, unknown>).formkit || (formElement as Record<string, unknown>).$formkit,
    } as FormKitSchemaNode

    // Remove the original formkit property to avoid duplication
    delete (formkitNode as Record<string, unknown>).formkit

    if (formkitNode?.label && typeof formkitNode.label === 'string') {
      formkitNode.label = formkitNode.label.replace(pattern, (match: string) => {
        const key = match.substring(1)
        return data.value[key] || match
      })
    }
    return formkitNode
  })
})

async function submitHandler() {
  emit('submit', data.value)
}
</script>

<style scoped>
.content {
  @apply font-light text-xs
}
.content :deep(.formkit-outer){
  @apply pt-3 pb-1;
}
.content :deep(h1) {
  @apply pt-3 pb-1 text-xl font-bold;
}

.content :deep(h2) {
  @apply pt-3 pb-1 text-lg font-bold;
}

.content :deep(h3) {
  @apply pt-3 pb-1 text-base font-bold;
}

.content :deep(h4) {
  @apply pt-3 pb-1 font-bold;
}

.content :deep(h5) {
  @apply pt-3 pb-1 font-bold;
}

.content :deep(h6) {
  @apply pt-3 pb-1 font-bold;
}

.content :deep(p) {
  @apply pt-3 pb-1 ;
}

.content :deep(blockquote) {
  @apply px-4 py-3 my-4 italic border-s-4 dark:border-gray-500/20 dark:bg-gray-800/20;
}

.content :deep(ul) {
  @apply list-disc list-outside mt-2;
}

.content :deep(ol) {
  @apply list-decimal list-outside mt-2;
}

.content :deep(ul > li) {
  @apply ml-4 mt-2;
}

.content :deep(ol > li) {
  @apply ml-6 mt-2;
}

.content :deep(strong) {
  @apply font-bold;
}

.content :deep(p a) {
  @apply  border-b border-dotted border-gray-400  after:content-['↗'] after:pl-[1px];
}
.content :deep(ul a) {
  @apply  border-b border-dotted border-gray-400  after:content-['↗'] after:pl-[1px];
}
.content :deep(table) {
  @apply my-8;
}
.content :deep(th) {
  @apply border border-surface-200 dark:border-surface-500 p-2 text-left font-bold bg-surface-100 dark:bg-surface-800;
}
.content :deep(td) {
  @apply border border-surface-200 dark:border-surface-500 p-2 text-left;
}
</style>
