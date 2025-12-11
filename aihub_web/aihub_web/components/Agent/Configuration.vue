<template>
  <Panel
    :header="title"
    toggleable
  >
    <p class="text-xs dark:text-surface-500">
      {{ description }}
    </p>
    <div class="content pt-6 max-w-2xl">
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
    <pre class="overflow-auto max-h-96 max-w-2xl text-xs bg-surface-900 p-4 rounded-lg mt-4">{{ data }}</pre>
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

  function transformElement(formElement: FormkitElement): FormKitSchemaNode | FormKitSchemaNode[] {
    const elementRecord = formElement as Record<string, unknown>
    const formkitType = elementRecord.formkit || elementRecord.$formkit

    // Handle group elements - wrap with visual container if label exists
    if (formkitType === 'group') {
      const children = (elementRecord.children as FormkitElement[] || []).flatMap(transformElement)
      const groupNode: FormKitSchemaNode = {
        $formkit: 'group',
        name: elementRecord.name as string,
        children: children as FormKitSchemaNode[],
      }

      // If group has a label, wrap it in a visual fieldset-like structure
      if (elementRecord.label) {
        return [
          {
            $el: 'fieldset',
            attrs: {
              class: 'formkit-group-fieldset border border-surface-300 dark:border-surface-600 rounded-lg p-4 mb-4',
            },
            children: [
              {
                $el: 'legend',
                attrs: {
                  class: 'text-sm font-semibold px-2 text-surface-700 dark:text-surface-300',
                },
                children: elementRecord.label as string,
              },
              groupNode,
            ],
          },
        ] as FormKitSchemaNode[]
      }

      return groupNode
    }

    const formkitNode = {
      ...formElement,
      $formkit: formkitType,
    } as FormKitSchemaNode

    // Remove the original formkit property to avoid duplication
    delete (formkitNode as Record<string, unknown>).formkit

    // Replace template variables in labels
    if (formkitNode?.label && typeof formkitNode.label === 'string') {
      formkitNode.label = formkitNode.label.replace(pattern, (match: string) => {
        const key = match.substring(1)
        return data.value[key] || match
      })
    }


    // Recursively transform children for any other elements with children
    const nodeRecord = formkitNode as Record<string, unknown>
    if (nodeRecord.children && Array.isArray(nodeRecord.children)) {
      nodeRecord.children = (nodeRecord.children as FormkitElement[]).flatMap(transformElement)
    }

    return formkitNode
  }

  return props.form.flatMap(transformElement)
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

.content :deep(.formkit-group-fieldset) {
  @apply border border-surface-300 dark:border-surface-600 rounded-lg p-4 mb-4 max-w-2xl;
}

.content :deep(.formkit-group-fieldset legend) {
  @apply text-sm font-semibold px-2 text-surface-700 dark:text-surface-300;
}

.content :deep(.formkit-group-fieldset .formkit-group-fieldset) {
  @apply ml-2 mt-2;
}

.content :deep(.formkit-slider-value-input) {
  @apply w-20;
}

.content :deep(.formkit-slider-value-input .p-inputnumber-input) {
  @apply text-center text-sm;
}
</style>
