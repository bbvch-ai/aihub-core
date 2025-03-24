<template>
  <div class="flex h-screen flex-col md:flex-row">
    <div class="order-2 flex h-3/5 w-full items-center justify-center bg-neutral-950 p-10 text-4xl text-stone-300 md:order-1 md:h-auto md:w-3/5">
      <span>Erleben Sie die Zukunft der künstlichen Intelligenz</span>
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
            alt="Logo of company"
            class="w-32 rounded lg:w-32"
          >
        </a>
        <div class="flex flex-col gap-2 text-center">
          <h2 class="text-xl text-white">
            Willkommen im AI Hub von {{ companyName }}
          </h2>
          <p class="text-stone-400">
            Bitte loggen Sie sich ein
          </p>
        </div>
        <Button
          label="Login with Microsoft"
          icon="pi pi-microsoft"
          icon-pos="right"
          class="!bg-white !text-black"
          @click="login"
        />
      </div>
      <a
        href="https://bbv.ch/services/generative-ai/"
        target="_blank"
        rel="noopener noreferrer"
        class="hidden text-stone-400 sm:block"
      >
        Individuelle KI-Lösungen für Ihr Unternehmen
      </a>
    </div>
  </div>
</template>

<script setup lang="ts">
import logo from '@core/assets/images/logo.png'

definePageMeta({
  layout: 'anonymous',
})

// In a real-world scenario, you might retrieve organization info.
// For now, we use a static default.
const companyName = 'bbv Software Services AG'

const login = () => {
  const { $auth } = useNuxtApp()
  $auth.signinRedirect()
}
</script>

<style scoped>
/* You can add additional styling if needed */
</style>
