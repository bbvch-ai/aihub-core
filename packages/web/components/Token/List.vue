<template>
  <DataTable
    :value="tokens"
    data-key="id"
    size="small"
  >
    <Column
      field="name"
      :header="t('token.list.name')"
      body-class="[overflow-wrap:anywhere]"
    />
    <Column
      field="created_at"
      :header="t('token.list.created')"
    >
      <template #body="{ data }">
        {{ formatDateTime(data.created_at) }}
      </template>
    </Column>
    <Column
      field="expiry_date"
      :header="t('token.list.expires')"
    >
      <template #body="{ data }">
        <div class="flex flex-wrap items-center gap-2">
          <span>{{ formatDate(data.expiry_date) }}</span>
          <Tag
            :value="t(`token.status.${statusOf(data)}`)"
            :severity="STATUS_SEVERITY[statusOf(data)]"
          />
        </div>
      </template>
    </Column>
    <Column
      field="last_used_at"
      :header="t('token.list.last_used')"
    >
      <template #body="{ data }">
        <span v-if="data.last_used_at">{{ formatDateTime(data.last_used_at) }}</span>
        <span
          v-else
          class="text-surface-500"
        >{{ t('token.list.never_used') }}</span>
      </template>
    </Column>
    <Column body-class="text-right">
      <template #body="{ data }">
        <Button
          v-tooltip.top="t('token.revoke.button')"
          icon="pi pi-trash"
          severity="danger"
          text
          rounded
          :aria-label="t('token.revoke.button')"
          @click="emit('revoke', data)"
        />
      </template>
    </Column>
  </DataTable>
</template>

<script setup lang="ts">
import { useNow } from '@vueuse/core'
import { addDays } from 'date-fns'

import type { TokenResponse } from '@core/sdk/client'

type TokenStatus = 'active' | 'expiring' | 'expired'

const EXPIRY_WARNING_DAYS = 7
const STATUS_SEVERITY: Record<TokenStatus, string> = { active: 'success', expiring: 'warn', expired: 'danger' }

defineProps<{
  tokens: TokenResponse[]
}>()

const emit = defineEmits<{
  revoke: [token: TokenResponse]
}>()

const { t } = useI18n()
const now = useNow({ interval: 60_000 })

const formatDate = (date: Date) => useDateFormat(date, 'DD.MM.YYYY').value
const formatDateTime = (date: Date) => useDateFormat(date, 'DD.MM.YYYY HH:mm').value

const statusOf = (token: TokenResponse): TokenStatus => {
  if (token.expiry_date <= now.value) return 'expired'
  if (token.expiry_date <= addDays(now.value, EXPIRY_WARNING_DAYS)) return 'expiring'
  return 'active'
}
</script>
