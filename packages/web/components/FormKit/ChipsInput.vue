<template>
  <div class="flex flex-col gap-2">
    <InputText
      v-model="draft"
      :placeholder="placeholder"
      class="w-full"
      @keydown.enter.stop.prevent="commitDraft"
      @keyup.enter.stop.prevent
      @keypress.enter.stop.prevent
      @blur="commitDraft"
    />
    <div
      v-if="chips.length > 0"
      class="flex flex-wrap gap-2"
    >
      <Chip
        v-for="value in chips"
        :key="value"
        :label="value"
        removable
        @remove="removeChip(value)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
interface ChipsInputProps {
  context: {
    node: { input: (value: string[]) => void }
    value?: string[] | null
    placeholder?: string
  }
}

const props = defineProps<ChipsInputProps>()

const placeholder = computed(() => props.context.placeholder)
const draft = ref('')

const chips = computed<string[]>({
  get: () => props.context.value ?? [],
  set: (value: string[]) => props.context.node.input(value),
})

function commitDraft() {
  const trimmed = draft.value.trim()
  draft.value = ''
  if (!trimmed)
    return
  if (chips.value.includes(trimmed))
    return
  chips.value = [...chips.value, trimmed]
}

function removeChip(value: string) {
  chips.value = chips.value.filter(v => v !== value)
}
</script>
