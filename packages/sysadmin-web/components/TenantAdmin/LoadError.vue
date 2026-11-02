<template>
  <Message
    :severity="isNotMember ? 'warn' : 'error'"
    :closable="false"
  >
    {{ isNotMember
      ? t('tenant_admin.state.not_member_message', { tenantId })
      : t('tenant_admin.load_error') }}
  </Message>
</template>

<script setup lang="ts">
const props = defineProps<{
  error: unknown
  tenantId: string
}>()

const { t } = useI18n()

// Tenant-scoped routes answer 403 only after accepting the caller's login, when the account is outside the
// tenant's Keycloak group — the sysadmin role grants rights inside a tenant, not membership of it.
const isNotMember = computed(() => {
  const err = props.error as { statusCode?: number, status?: number } | null | undefined
  return (err?.statusCode ?? err?.status) === 403
})
</script>
