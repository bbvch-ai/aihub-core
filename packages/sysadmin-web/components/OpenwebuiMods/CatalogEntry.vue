<template>
  <section class="rounded-xl border border-surface-200 p-4 dark:border-surface-700">
    <div class="flex items-start justify-between gap-4">
      <div class="min-w-0">
        <h3 class="break-words font-semibold">
          {{ manifest?.name ?? selection.mod_id }}
        </h3>
        <p class="text-sm text-surface-500">
          {{ manifest?.version }}<span v-if="entry?.builtin"> · {{ t('openwebui_mods.automatic_version') }}</span>
        </p>
        <p
          v-if="manifest?.description"
          class="mt-1 text-sm"
        >
          {{ manifest.description }}
        </p>
      </div>
      <ToggleSwitch
        v-model="selection.enabled"
        class="shrink-0"
        :aria-label="t('openwebui_mods.enable', { name: manifest?.name ?? selection.mod_id })"
      />
    </div>
    <p
      v-if="requiresRestart"
      class="mt-3 text-sm text-surface-500"
    >
      {{ t('openwebui_mods.global.mod_restart') }}
    </p>
    <details
      v-if="form?.length"
      class="mt-4"
    >
      <summary class="cursor-pointer text-sm">
        {{ t('openwebui_mods.settings') }}
      </summary>
      <p
        :id="`${selection.mod_id}-help`"
        class="my-2 text-sm text-surface-500"
      >
        {{ t(globalScope ? 'openwebui_mods.global.settings_help' : 'openwebui_mods.settings_help') }}
      </p>
      <FormKitDynamicConfiguration
        :key="formKey"
        :form="form"
        :initial-data="initialSettings"
        embedded
        @change="updateSettings"
        @valid="valid = $event"
      />
    </details>
  </section>
</template>

<script setup lang="ts">
import { getFormkitType, type FormElement } from '@core/composables/form/useFormKitTransform'

import type { OpenWebuiModSelection, OpenWebuiModCatalogEntry } from '~/sdk/client'

const selection = defineModel<OpenWebuiModSelection>({ required: true })
const valid = defineModel<boolean>('valid', { default: true })
const props = defineProps<{ entry?: OpenWebuiModCatalogEntry, globalScope?: boolean }>()
const { t } = useI18n()
const formId = useId().replace(/\W/g, '_')
const manifest = computed(() => props.entry?.manifest)
const formKey = computed(() => `${formId}:${props.entry?.source_revision ?? ''}`)
watch(formKey, () => {
  valid.value = true
})
// Each mod owns its FormKit IDs, including synthetic nullable toggles.
function scopeFields(fields: Record<string, unknown>[], path = ''): FormElement[] {
  return fields.map(field => ({
    ...field,
    ...(getFormkitType(field) === 'localeInput' ? { allowTranslation: false } : {}),
    id: `${formId}__${path}${field.name}`,
    ...(Array.isArray(field.children) ? { children: scopeFields(field.children, `${path}${field.name}__`) } : {}),
  }))
}
const form = computed(() => props.entry?.settings_form ? scopeFields(props.entry.settings_form) : undefined)
const initialSettings = computed(() => ({ ...props.entry?.manifest.default_settings, ...selection.value.settings }))
function mergeFields(saved: Record<string, unknown>, changed: Record<string, unknown>, fields: FormElement[]): Record<string, unknown> {
  const result = { ...saved }
  for (const field of fields) {
    const name = field.name as string
    if (!(name in changed)) continue
    const value = changed[name]
    result[name] = getFormkitType(field) === 'group' && value && typeof value === 'object' && !Array.isArray(value)
      ? mergeFields((saved[name] ?? {}) as Record<string, unknown>, value as Record<string, unknown>, field.children as FormElement[])
      : value
  }
  return result
}
function updateSettings(settings: Record<string, unknown>) {
  // Preserve saved fields absent from this version's form, including nested groups.
  selection.value = { ...selection.value, settings: mergeFields(selection.value.settings ?? {}, settings, form.value ?? []) as OpenWebuiModSelection['settings'] }
}
const requiresRestart = computed(() => manifest.value?.backend_restart_required || Boolean(manifest.value?.backend_overrides?.['open_webui.main:lifespan']))
</script>
