<template>
  <AuthLoginPanel>
    <template #heading>
      {{ t('auth.login.welcome', { companyName }) }}
    </template>
    <template #message>
      {{ t('auth.login.pleaseLogin') }}
    </template>

    <ProgressSpinner
      v-if="isLoading"
      class="!h-8 !w-8"
    />
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
const { authProviders, isLoading } = useAuthProviders()

const companyName = 'bbv Software Services AG'
</script>
