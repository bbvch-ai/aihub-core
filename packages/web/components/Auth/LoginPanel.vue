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
            <slot name="heading" />
          </h2>
          <p class="text-surface-400">
            <slot name="message" />
          </p>
        </div>
        <div class="flex flex-col gap-3">
          <slot />
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

const { t } = useI18n()
</script>
