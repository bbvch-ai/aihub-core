<template>
  <AuthLoginPanel>
    <template #heading>
      {{ t('auth.login.welcome', { companyName }) }}
    </template>
    <template #message>
      <template v-if="!isLoading">
        {{ welcomePage ? t('auth.login.useOrganisationLink') : t('auth.login.pleaseLogin') }}
      </template>
    </template>

    <ProgressSpinner
      v-if="isLoading"
      class="!h-8 !w-8"
    />
    <template v-else-if="welcomePage">
      <Button
        v-if="offersKeycloakLogin"
        :label="t('auth.login.adminLogin')"
        variant="text"
        severity="secondary"
        size="small"
        class="!text-surface-400"
        @click="login()"
      />
    </template>
    <template v-else>
      <Button
        v-for="idp in authProviders ?? []"
        :key="idp.alias"
        :label="t('auth.login.loginWith', { provider: idp.display_name })"
        :icon="`pi ${idp.icon}`"
        icon-pos="right"
        class="!bg-white !text-black"
        @click="login(idp.alias || undefined)"
      />
      <Button
        v-if="(authProviders?.length ?? 0) === 0"
        :label="t('auth.login.title')"
        icon="pi pi-sign-in"
        icon-pos="right"
        class="!bg-white !text-black"
        @click="login()"
      />
    </template>
  </AuthLoginPanel>
</template>

<script setup lang="ts">
definePageMeta({
  layout: 'anonymous',
})

const { t } = useI18n()
const { login } = useAuth()
const { welcomePage, authProviders, isLoading } = useAuthProviders()

// A welcome-page instance lists no tenant provider; the direct Keycloak login
// (empty alias) is all that is left, and it is how administrators get in.
const offersKeycloakLogin = computed(() => authProviders.value?.some(idp => idp.alias === '') ?? false)

const companyName = 'bbv Software Services AG'
</script>
