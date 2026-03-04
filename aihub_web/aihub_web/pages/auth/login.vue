<template>
  <div class="flex h-screen flex-col md:flex-row">
    <div class="order-2 flex h-3/5 w-full items-center justify-center bg-neutral-950 p-10 text-4xl text-surface-300 md:order-1 md:h-auto md:w-3/5">
      <span>{{ t('auth.login.tagline') }}</span>
    </div>

    <!-- Right Panel: Login -->
    <div class="order-1 flex h-2/5 w-full flex-col items-center justify-between bg-zinc-900 p-6 md:order-2 md:h-full md:w-2/5">
      <div />
      <div class="flex flex-col items-center gap-8">
        <a
          href="https://ai-hub.bbv.ch"
          target="_blank"
          rel="noopener noreferrer"
        >
          <img
            :src="logo"
            :alt="t('auth.login.logoAlt')"
            class="w-32 rounded lg:w-32"
          >
        </a>
        <div class="flex flex-col gap-2 text-center">
          <h2 class="text-xl text-white">
            {{ t('auth.login.welcome', { companyName }) }}
          </h2>
          <p class="text-surface-400">
            {{ t('auth.login.pleaseLogin') }}
          </p>
        </div>
        <div class="flex flex-col gap-3">
          <ProgressSpinner v-if="isLoading" class="!h-8 !w-8" />
          <template v-else>
            <Button
              v-for="idp in authProviders"
              :key="idp.alias"
              :label="t('auth.login.loginWith', { provider: idp.display_name })"
              :icon="`pi ${idp.icon}`"
              icon-pos="right"
              class="!bg-white !text-black"
              @click="login(idp.alias || undefined)"
            />
            <Button
              v-if="authProviders.length === 0"
              :label="t('auth.login.title')"
              icon="pi pi-sign-in"
              icon-pos="right"
              class="!bg-white !text-black"
              @click="login()"
            />
          </template>
        </div>
      </div>
      <a
        href="https://bbv.ch/services/generative-ai/"
        target="_blank"
        rel="noopener noreferrer"
        class="hidden text-surface-400 sm:block"
      >
        {{ t('auth.login.customSolutions') }}
      </a>
    </div>
  </div>
</template>

<script setup lang="ts">
import logo from '@core/assets/images/logo.png'

definePageMeta({
  layout: 'anonymous',
})

const { t } = useI18n()
const { login } = useAuth()
const { authProviders, isLoading } = useAuthProviders()

const companyName = 'bbv Software Services AG'
</script>
