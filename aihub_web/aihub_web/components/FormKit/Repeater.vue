<template>
  <fieldset class="mb-4 rounded-lg border border-surface-300 p-4 dark:border-surface-600">
    <legend class="px-2 text-sm font-semibold text-surface-700 dark:text-surface-300">
      {{ label }}
    </legend>

    <!-- Repeater items -->
    <div class="flex flex-col gap-3">
      <div
        v-for="(item, index) in items"
        :key="index"
        class="relative rounded-lg border border-surface-200 p-4 dark:border-surface-700"
      >
        <!-- Item header with index and remove button -->
        <div class="mb-3 flex items-center justify-between">
          <span class="text-sm font-medium text-surface-600 dark:text-surface-400">
            #{{ index + 1 }}
          </span>
          <Button
            type="button"
            icon="pi pi-trash"
            severity="danger"
            text
            size="small"
            :disabled="isRemoveDisabled"
            @click.prevent.stop="removeItem(index)"
          />
        </div>

        <!-- Item content - render children schema for each item -->
        <FormKit
          v-if="modelValue"
          :id="`${name}-${index}`"
          v-model="modelValue[index]"
          type="group"
        >
          <FormKitSchema
            :schema="childrenSchema"
            :data="modelValue[index]"
          />
        </FormKit>
      </div>
    </div>

    <!-- Add button -->
    <Button
      type="button"
      :label="addLabel || 'Add Item'"
      icon="pi pi-plus"
      size="small"
      class="mt-3"
      :disabled="isAddDisabled"
      @click.prevent.stop="addItem"
    />
  </fieldset>
</template>

<script setup lang="ts">
import type { FormKitSchemaNode } from '@formkit/core'

const props = defineProps<{
  name: string
  label?: string
  addLabel?: string
  childrenSchema: FormKitSchemaNode[]
  min?: number
  max?: number
}>()

const modelValue = defineModel<Record<string, unknown>[]>({ default: () => [] })

// Ensure modelValue is always an array
const items = computed(() => modelValue.value || [])

// Check if add button should be disabled (only when max is a number and reached)
const isAddDisabled = computed(() => {
  if (typeof props.max !== 'number') return false
  return items.value.length >= props.max
})

// Check if remove button should be disabled (only when min is a number and reached)
const isRemoveDisabled = computed(() => {
  const minVal = typeof props.min === 'number' ? props.min : 0
  return items.value.length <= minVal
})

function addItem() {
  if (isAddDisabled.value) return
  if (!modelValue.value) {
    modelValue.value = []
  }
  modelValue.value.push({})
}

function removeItem(index: number) {
  if (!modelValue.value || isRemoveDisabled.value) return
  // Create new array to trigger reactivity
  modelValue.value = modelValue.value.filter((_, i) => i !== index)
}
</script>
