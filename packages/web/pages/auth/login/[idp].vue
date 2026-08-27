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
const route = useRoute()
const { login } = useAuth()
const { authProviders, isLoading } = useAuthProviders()

/**
 * The empty alias belongs to the synthetic "Keycloak" entry, which has no
 * kc_idp_hint and must therefore not be addressable through a tenant link.
 */
const requestedAlias = computed(() => String(route.params.idp ?? ''))
const provider = computed(() =>
  requestedAlias.value
    ? authProviders.value?.find(candidate => candidate.alias === requestedAlias.value)
    : undefined,
)

// Only decide once the query settled — an unknown, disabled or hidden alias
// (and a failed provider request) falls back to the all-providers page.
watch([isLoading, provider], ([providersLoading, matchedProvider]) => {
  if (!providersLoading && !matchedProvider) {
    navigateTo(`/${locale.value}/auth/login`, { replace: true })
  }
}, { immediate: true })
</script>
