<template>
  <StructuralScreen>
    <StructuralColumn
      :title="t('token.title')"
      :loading="tokensAreLoading"
    >
      <div class="flex flex-col gap-4">
        <div class="flex flex-wrap items-start justify-between gap-4">
          <p class="max-w-prose text-sm text-surface-600 dark:text-surface-300">
            {{ t('token.intro') }}
          </p>
          <Button
            icon="pi pi-plus"
            :label="t('token.create.button')"
            @click="createDialogVisible = true"
          />
        </div>

        <TokenList
          v-if="tokens?.length"
          :tokens="tokens"
          @revoke="confirmRevoke"
        />
        <div
          v-else
          class="flex flex-col items-center gap-2 rounded-xl border-2 border-dashed border-surface-300 p-8 text-center text-surface-500 dark:border-surface-600"
        >
          <i class="pi pi-key text-2xl" />
          <span>{{ t('token.list.empty') }}</span>
        </div>
      </div>
    </StructuralColumn>

    <TokenCreateDialog v-model="createDialogVisible" />
  </StructuralScreen>
</template>

<script setup lang="ts">
import type { TokenResponse } from '@core/sdk/client'

const { t } = useI18n()
const confirm = useConfirm()
const toast = useToast()

const { tenantId } = useTenant()
const { tokens, tokensAreLoading } = useTokens()
const { revokeToken } = useRevokeToken()

const createDialogVisible = ref(false)

const confirmRevoke = (token: TokenResponse) => {
  confirm.require({
    message: t('token.revoke.explanation', { name: token.name }),
    header: t('token.revoke.confirm'),
    icon: 'pi pi-exclamation-triangle',
    position: 'bottom',
    rejectProps: { label: t('token.revoke.cancel'), severity: 'secondary', outlined: true },
    acceptProps: { label: t('token.revoke.proceed'), severity: 'danger' },
    accept: async () => {
      await revokeToken({ tokenId: token.id, tenantId: tenantId.value! })
      toast.add({ severity: 'success', summary: t('token.revoke.success'), detail: token.name, life: 3000 })
    },
  })
}
</script>
