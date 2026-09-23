<template>
  <StructuralScreen>
    <StructuralColumn
      :title="t('tenant_settings.title')"
      :loading="isPending && !error"
      size="small"
    >
      <Message
        v-if="error"
        severity="error"
        :closable="false"
      >
        {{ t('tenant_settings.load_error') }}
      </Message>
      <FormKit
        v-else-if="draft"
        type="form"
        :actions="false"
        @submit="save"
      >
        <FormKit
          v-model="draft.chat_disclaimer"
          type="localeInput"
          name="chat_disclaimer"
          input-type="textarea"
          :label="t('tenant_settings.disclaimer')"
          :help="t('tenant_settings.help')"
          :placeholder="placeholder"
          validation="localeRequired|disclaimerLength"
          :validation-rules="{ disclaimerLength }"
          :validation-messages="{ disclaimerLength: t('tenant_settings.too_long') }"
        />
        <Message
          v-if="saveFailed"
          severity="error"
          :closable="false"
          class="mb-4"
        >
          {{ t('tenant_settings.save_error') }}
        </Message>
        <div class="flex justify-end">
          <Button
            type="submit"
            :label="t('tenant_settings.save')"
            icon="pi pi-save"
            :loading="isSaving"
            :disabled="isSaving"
          />
        </div>
      </FormKit>
    </StructuralColumn>
  </StructuralScreen>
</template>

<script setup lang="ts">
import { isEqual } from 'lodash-es'

import type { TenantSettingsDto } from '@core/sdk/client'

definePageMeta({ key: route => String(route.params.tenant) })

const { t } = useI18n()
const { tenantId } = useTenant()
const { settings, isPending, error } = useTenantSettings()
const { saveSettings, isSaving } = useUpdateTenantSettings()
const toast = useToast()
const draft = ref<TenantSettingsDto>()
const saveFailed = ref(false)
const placeholder = computed(() => Object.fromEntries(
  ['de', 'en', 'fr', 'it'].map(locale => [locale, t('tenant_settings.disclaimer')]),
))

// A background refresh must not discard an admin's unsaved edits.
watch(settings, (value, previous) => {
  if (value && (!draft.value || isEqual(draft.value, previous))) draft.value = structuredClone(toRaw(value))
}, { immediate: true })

function disclaimerLength(node: { value: unknown }) {
  return Object.values((node.value ?? {}) as Record<string, string | null>)
    .every(value => !value || [...value.trim()].length <= 400)
}

async function save() {
  if (!draft.value || !tenantId.value || isSaving.value) return
  saveFailed.value = false
  try {
    await saveSettings({ tenantId: tenantId.value, settings: structuredClone(toRaw(draft.value)) })
    toast.add({ severity: 'success', summary: t('tenant_settings.saved'), life: 3000 })
  }
  catch {
    saveFailed.value = true
  }
}
</script>
