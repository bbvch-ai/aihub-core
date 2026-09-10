<template>
  <div class="flex items-center gap-3">
    <!-- Icon preview (fixed width to prevent layout shift) -->
    <div class="flex w-8 shrink-0 items-center justify-center">
      <Icon
        v-if="selectedIcon"
        :name="selectedIcon"
        class="text-2xl text-surface-700 dark:text-surface-200"
      />
      <Icon
        v-else
        name="mage:image"
        class="text-2xl text-surface-300 dark:text-surface-600"
      />
    </div>

    <!-- Editable Select -->
    <Select
      v-model="selectedIcon"
      :aria-label="placeholder"
      :options="iconOptions"
      :editable="true"
      :placeholder="placeholder"
      option-label="name"
      option-value="name"
      class="grow"
    >
      <!-- Option template - shows icon + name for each option -->
      <template #option="{ option }">
        <div class="flex items-center gap-2">
          <Icon
            :name="option.name"
            class="shrink-0 text-lg"
          />
          <span>{{ option.name }}</span>
        </div>
      </template>
    </Select>
  </div>
</template>

<script setup lang="ts">
interface IconSelectorProps {
  context: {
    node: {
      input: (value: string) => void
    }
    value?: string
    attrs: Record<string, unknown>
    options?: string[]
    placeholder?: string
  }
}

const props = defineProps<IconSelectorProps>()

// Get options from context (passed from backend)
const options = computed(() => props.context.options ?? [])
const placeholder = computed(() => props.context.placeholder ?? 'Select or enter an icon...')

// Convert string options to objects for Select component
const iconOptions = computed(() =>
  options.value.map(name => ({ name })),
)

// Current selected icon value
const selectedIcon = computed({
  get: () => props.context.value ?? '',
  set: (newVal: string) => {
    props.context.node.input(newVal || '')
  },
})
</script>
