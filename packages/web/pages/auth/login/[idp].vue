<template>
  <AuthLoginPanel>
    <template #heading>
      <template v-if="provider">
        {{ t('auth.login.welcomeProvider', { provider: provider.display_name }) }}
      </template>
    </template>
    <template #message>
      <template v-if="provider">
        {{ t('auth.login.pleaseLoginWith', { provider: provider.display_name }) }}
      </template>
    </template>

    <Button
      v-if="provider"
      :label="t('auth.login.loginWith', { provider: provider.display_name })"
      :icon="`pi ${provider.icon}`"
      icon-pos="right"
      class="!bg-white !text-black"
      @click="login(provider.alias)"
    />
    <ProgressSpinner
      v-else
      class="!h-8 !w-8"
    />
  </AuthLoginPanel>
</template>

<script setup lang="ts">
definePageMeta({
  layout: 'anonymous',
})

const { t, locale } = useI18n()
const { login } = useAuth()
// The API never resolves the synthetic "Keycloak" entry (empty alias, no
// kc_idp_hint), so a tenant link can only ever name a federated provider.
const { provider, isLoading } = useAuthProvider()

// Only decide once the query settled — an unknown, disabled or link-only alias
// (and a failed provider request) falls back to the generic login page.
watch([isLoading, provider], ([providersLoading, matchedProvider]) => {
  if (!providersLoading && !matchedProvider) {
    navigateTo(`/${locale.value}/auth/login`, { replace: true })
  }
}, { immediate: true })
</script>
