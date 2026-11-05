<template>
  <div class="flex flex-col gap-1">
    <Checkbox
      :model-value="isAvailable ? Boolean(props.context.value) : false"
      :input-id="props.context.id"
      binary
      :disabled="props.context.disabled || !isAvailable"
      @update:model-value="value => props.context.node.input(Boolean(value))"
    />
    <!-- FormKit's own help class, so the note matches the help text below it in every form. -->
    <!-- eslint-disable tailwindcss/no-custom-classname -->
    <div
      v-if="!isAvailable"
      class="formkit-help"
    >
      {{ t('lib.modelGated.unavailable', { model: modelName ?? '' }) }}
    </div>
    <!-- eslint-enable tailwindcss/no-custom-classname -->
  </div>
</template>

<script setup lang="ts">
import type { ModelInfoDto } from '@core/sdk/client'
import type { FormKitNode } from '@formkit/core'

interface ModelGatedCheckboxProps {
  context: {
    node: FormKitNode
    id: string
    value?: boolean | null
    disabled?: boolean
    // Custom props are passed through context, not as direct Vue props
    modelRef?: string
    requires?: keyof ModelInfoDto
  }
}

const props = defineProps<ModelGatedCheckboxProps>()
const { t } = useI18n()

const { modelName, modelInfo } = useReferencedModel(props.context.node, () => props.context.modelRef)

// Only an explicit `false` gates: LiteLLM leaves most capability flags unset, and the API applies the same rule.
const isAvailable = computed(() => {
  const requires = props.context.requires
  return !requires || modelInfo.value?.[requires] !== false
})

// The stored value follows what is shown, so a profile switched to a model without the capability saves as off.
watch(isAvailable, (available) => {
  if (!available && props.context.value) props.context.node.input(false)
})
</script>
