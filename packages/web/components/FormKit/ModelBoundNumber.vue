<template>
  <div class="flex flex-col gap-1">
    <div
      v-if="hasOverride"
      class="flex items-center gap-2"
    >
      <Checkbox
        :model-value="overriding"
        :input-id="overrideCheckboxId"
        binary
        :disabled="props.context.disabled"
        @update:model-value="setOverriding"
      />
      <label
        :for="overrideCheckboxId"
        class="cursor-pointer"
      >
        {{ overrideLabelText }}
      </label>
    </div>
    <InputNumber
      :model-value="hasOverride && !overriding ? null : (props.context.value ?? null)"
      :input-id="props.context.id"
      :min="min"
      :max="effectiveMax"
      :step="step"
      :min-fraction-digits="minFractionDigits"
      :max-fraction-digits="maxFractionDigits"
      :use-grouping="useGrouping"
      :locale="numberLocale"
      :placeholder="placeholder"
      :disabled="props.context.disabled || (hasOverride && !overriding)"
      class="w-full"
      @update:model-value="value => props.context.node.input(value ?? null)"
    />
    <!-- FormKit's own help class: each form styles .formkit-help differently, and the hint must match the help text
         below it wherever it renders. -->
    <!-- eslint-disable tailwindcss/no-custom-classname -->
    <div
      v-if="hint"
      class="formkit-help"
    >
      {{ hint }}
    </div>
    <!-- eslint-enable tailwindcss/no-custom-classname -->
  </div>
</template>

<script setup lang="ts">
import { createMessage } from '@formkit/core'

import type { ModelInfoDto } from '@core/sdk/client'
import type { FormKitNode } from '@formkit/core'

type ModelInfoKey = keyof ModelInfoDto

interface ModelBoundNumberProps {
  context: {
    node: FormKitNode
    id: string
    value?: number | null
    disabled?: boolean
    // Custom props are passed through context, not as direct Vue props
    modelRef?: string
    maxFrom?: ModelInfoKey
    defaultFrom?: ModelInfoKey
    fallbackDefault?: number
    overrideLabel?: string
    fillFactor?: number
    min?: number
    max?: number
    step?: number
    minFractionDigits?: number
    maxFractionDigits?: number
    useGrouping?: boolean
  }
}

const props = defineProps<ModelBoundNumberProps>()
const { t, locale } = useI18n()

const ERROR_MESSAGE_KEY = 'modelMaximum'
const REQUIRED_MESSAGE_KEY = 'overrideRequired'

const min = computed(() => props.context.min)
const step = computed(() => props.context.step)
const minFractionDigits = computed(() => props.context.minFractionDigits ?? 0)
const maxFractionDigits = computed(() => props.context.maxFractionDigits ?? 6)
const useGrouping = computed(() => props.context.useGrouping ?? true)

// The German, French and Italian UI is Swiss, so numbers are grouped the Swiss way (155’648); the input and the hint
// share one locale so they never show different separators.
const SWISS_NUMBER_LOCALES: Record<string, string> = { de: 'de-CH', fr: 'fr-CH', it: 'it-CH' }
const numberLocale = computed(() => SWISS_NUMBER_LOCALES[locale.value] ?? locale.value)
const formatNumber = (value: number) => new Intl.NumberFormat(numberLocale.value).format(value)
// A decimal setting such as a temperature reads "1.0", not "1", so its default is not mistaken for a count.
const formatDefault = (value: number) => new Intl.NumberFormat(numberLocale.value, {
  minimumFractionDigits: (props.context.step ?? 1) < 1 ? 1 : 0,
}).format(value)

const { modelName, modelInfo } = useReferencedModel(props.context.node, () => props.context.modelRef)

function numberFromModel(key: ModelInfoKey | undefined): number | null {
  const value = key ? modelInfo.value?.[key] : undefined
  return typeof value === 'number' ? value : null
}

const modelMax = computed(() => numberFromModel(props.context.maxFrom))
const modelDefault = computed(() => numberFromModel(props.context.defaultFrom))

// The share of the model's limit the runtime fills is the bound itself, as in the API's `maximum_for`: a value above it
// would behave exactly like it, so the field never shows a number the run does not use.
const filledMaximum = computed(() => {
  const fillFactor = props.context.fillFactor
  if (modelMax.value === null) return null
  return fillFactor ? Math.floor(modelMax.value * fillFactor) : modelMax.value
})

const effectiveMax = computed(() => {
  const staticMax = props.context.max
  if (filledMaximum.value === null) return staticMax
  return staticMax === undefined ? filledMaximum.value : Math.min(staticMax, filledMaximum.value)
})

// With an override label the unset state is this component's own: the checkbox decides whether the field holds a
// value, and while it is off the disabled input shows what applies instead (the model's default, the platform's
// fallback, or the provider's choice), so the admin sees it before deciding to override.
const hasOverride = computed(() => Boolean(props.context.overrideLabel))
const overrideCheckboxId = computed(() => `${props.context.id}-override`)
// A budget has no curated default: left unset, the runtime fills the model's limit less its margin.
const filledBudget = computed(() => props.context.defaultFrom || !props.context.fillFactor ? null : filledMaximum.value)
const appliedDefault = computed(() => modelDefault.value ?? filledBudget.value ?? props.context.fallbackDefault ?? null)
const appliedDefaultText = computed(() => appliedDefault.value === null
  ? t('lib.modelBound.providerDefault')
  : formatDefault(appliedDefault.value))
const overrideLabelText = computed(() => `${props.context.overrideLabel} (${appliedDefaultText.value})`)

// Kept apart from the value: ticking the box for a field whose default is unknown leaves it empty until the admin
// types one, and it must stay ticked meanwhile.
const overriding = ref(props.context.value !== null && props.context.value !== undefined)
watch(() => props.context.value, (value) => {
  if (value !== null && value !== undefined) overriding.value = true
})

// Starting from the default the admin was shown is what an override usually adjusts; unticking returns the field to
// "not set", so the model's default applies again and follows later model changes.
function setOverriding(enabled: boolean) {
  overriding.value = enabled
  props.context.node.input(enabled ? appliedDefault.value : null)
}

const placeholder = computed(() => {
  if (hasOverride.value) return appliedDefaultText.value
  return modelDefault.value === null
    ? undefined
    : t('lib.modelBound.defaultPlaceholder', { value: formatNumber(modelDefault.value) })
})

watch([overriding, () => props.context.value], ([enabled, value]) => {
  props.context.node.store.remove(REQUIRED_MESSAGE_KEY)
  if (!hasOverride.value || !enabled || (value !== null && value !== undefined)) return
  props.context.node.store.set(createMessage({
    blocking: true,
    key: REQUIRED_MESSAGE_KEY,
    type: 'error',
    value: t('lib.modelBound.overrideRequired'),
    visible: true,
  }))
}, { immediate: true })

// The hint names the model's own limit next to the bound, so a maximum below the published window is not mistaken
// for a wrong figure.
const hint = computed(() => {
  if (modelMax.value === null || filledMaximum.value === null || !modelName.value) return undefined
  const fillFactor = props.context.fillFactor
  if (!fillFactor) return t('lib.modelBound.maximumHint', { maximum: formatNumber(modelMax.value), model: modelName.value })
  return t('lib.modelBound.maximumHintWithFill', {
    maximum: formatNumber(filledMaximum.value),
    model: modelName.value,
    modelMaximum: formatNumber(modelMax.value),
    percent: new Intl.NumberFormat(numberLocale.value, { style: 'percent' }).format(fillFactor),
  })
})

// A value saved for a larger model is shown as is and blocks submission rather than being clamped, so switching
// models never changes a stored budget behind the admin's back.
watch([() => props.context.value, effectiveMax], ([value, maximum]) => {
  props.context.node.store.remove(ERROR_MESSAGE_KEY)
  if (typeof value !== 'number' || maximum === undefined || value <= maximum) return
  props.context.node.store.set(createMessage({
    blocking: true,
    key: ERROR_MESSAGE_KEY,
    type: 'error',
    value: t('lib.modelBound.aboveMaximum', { maximum: formatNumber(maximum), model: modelName.value ?? '' }),
    visible: true,
  }))
}, { immediate: true })
</script>
