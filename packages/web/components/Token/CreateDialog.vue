<template>
  <Dialog
    v-model:visible="visible"
    modal
    :header="created ? t('token.created.title') : t('token.create.title')"
    :style="{ width: '40rem' }"
    :closable="!isCreating"
    @after-hide="reset"
  >
    <div
      v-if="created"
      class="flex flex-col gap-4"
    >
      <Message
        severity="warn"
        :closable="false"
      >
        {{ t('token.created.warning') }}
      </Message>
      <div class="flex flex-col gap-2">
        <label
          for="created-token-value"
          class="text-sm font-medium"
        >{{ created.name }}</label>
        <InputGroup>
          <InputText
            id="created-token-value"
            :model-value="created.token"
            readonly
            class="font-mono"
            @focus="($event.target as HTMLInputElement).select()"
          />
          <Button
            :icon="copied ? 'pi pi-check' : 'pi pi-copy'"
            :label="copied ? t('token.created.copied') : t('token.created.copy')"
            @click="copyToken(created.token)"
          />
        </InputGroup>
      </div>
      <small class="text-surface-500">{{ t('token.created.usage') }}</small>
    </div>

    <div
      v-else
      class="flex flex-col gap-4"
    >
      <div class="flex flex-col gap-2">
        <label
          for="token-name-input"
          class="text-sm font-medium"
        >
          {{ t('token.create.name.label') }}
          <span class="ml-1 text-xs text-red-500">*</span>
        </label>
        <InputText
          id="token-name-input"
          v-model="name"
          :maxlength="nameMaxLength"
          :placeholder="t('token.create.name.placeholder')"
          :disabled="isCreating"
          @keyup.enter="handleCreate"
        />
        <small class="text-surface-500">{{ t('token.create.name.help') }}</small>
      </div>

      <div class="flex flex-col gap-2">
        <span class="text-sm font-medium">{{ t('token.create.expiry.label') }}</span>
        <SelectButton
          v-model="expiryChoice"
          :options="expiryOptions"
          option-label="label"
          option-value="value"
          :allow-empty="false"
          :disabled="isCreating"
          class="flex-wrap"
          :pt="{ pcToggleButton: { label: { class: 'whitespace-nowrap' } } }"
        />
        <DatePicker
          v-if="expiryChoice === CUSTOM_EXPIRY"
          v-model="customExpiry"
          :min-date="tomorrow"
          date-format="dd.mm.yy"
          :placeholder="t('token.create.expiry.custom_placeholder')"
          :disabled="isCreating"
          show-icon
        />
        <small
          v-if="expiryDate"
          class="text-surface-500"
        >
          {{ t('token.create.expiry.help', { date: useDateFormat(expiryDate, 'DD.MM.YYYY').value }) }}
        </small>
      </div>

      <small
        v-if="error"
        class="text-red-500"
      >{{ error }}</small>
    </div>

    <template #footer>
      <div class="flex justify-end gap-2">
        <Button
          v-if="created"
          :label="t('token.created.done')"
          @click="visible = false"
        />
        <template v-else>
          <Button
            :label="t('token.create.cancel')"
            severity="secondary"
            outlined
            :disabled="isCreating"
            @click="visible = false"
          />
          <Button
            :label="t('token.create.submit')"
            :disabled="!canSubmit"
            :loading="isCreating"
            @click="handleCreate"
          />
        </template>
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { CreateTokenRequestSchema } from '@core/sdk/client/schemas.gen'
import { useClipboard } from '@vueuse/core'
import { addDays, endOfDay, startOfDay } from 'date-fns'

import type { CreateTokenResponse } from '@core/sdk/client'

const CUSTOM_EXPIRY = 'custom'
const PRESET_DAYS = [30, 90, 180, 365] as const
const DEFAULT_DAYS = 90

type ExpiryChoice = (typeof PRESET_DAYS)[number] | typeof CUSTOM_EXPIRY

const visible = defineModel<boolean>({ required: true })

const { t } = useI18n()
const { tenantId } = useTenant()
const { createToken } = useCreateToken()
const { copy, copied } = useClipboard({ legacy: true })

const nameMaxLength = schemaMaxLength(CreateTokenRequestSchema, 'name')

const name = ref('')
const expiryChoice = ref<ExpiryChoice>(DEFAULT_DAYS)
const customExpiry = ref<Date | null>(null)
const isCreating = ref(false)
const error = ref('')
// Held only here, so closing the dialog is the end of the token's life in the browser.
const created = ref<CreateTokenResponse | null>(null)

const tomorrow = computed(() => startOfDay(addDays(new Date(), 1)))

const expiryOptions = computed(() => [
  ...PRESET_DAYS.map(days => ({ label: t(`token.create.expiry.preset_${days}`), value: days })),
  { label: t('token.create.expiry.custom'), value: CUSTOM_EXPIRY },
])

const expiryDate = computed<Date | null>(() => {
  if (expiryChoice.value !== CUSTOM_EXPIRY) return addDays(new Date(), expiryChoice.value)
  return customExpiry.value ? endOfDay(customExpiry.value) : null
})

const canSubmit = computed(() => !!name.value.trim() && !!expiryDate.value && !isCreating.value)

const handleCreate = async () => {
  if (!canSubmit.value) return

  isCreating.value = true
  error.value = ''
  try {
    created.value = await createToken({ name: name.value.trim(), expiresAt: expiryDate.value!, tenantId: tenantId.value! })
  }
  catch {
    error.value = t('token.create.error')
  }
  finally {
    isCreating.value = false
  }
}

const copyToken = async (token: string) => {
  try {
    await copy(token)
  }
  catch {
    // A browser that refuses clipboard access still lets the user copy a selection by hand.
    const input = document.getElementById('created-token-value') as HTMLInputElement | null
    input?.focus()
    input?.select()
  }
}

const reset = () => {
  created.value = null
  name.value = ''
  expiryChoice.value = DEFAULT_DAYS
  customExpiry.value = null
  error.value = ''
}
</script>
