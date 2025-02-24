<template>
  <div class="flex flex-col md:flex-row h-screen">
    <div class="md:order-1 order-2 h-3/5 md:h-auto md:w-3/5 w-full flex items-center justify-center bg-neutral-950 p-10 text-gray-300 text-4xl">
      <span>Erleben Sie die Zukunft der künstlichen Intelligenz</span>
    </div>

    <!-- Right Panel: Login -->
    <div class="md:order-2 order-1 h-2/5 md:h-full md:w-2/5 w-full flex flex-col items-center justify-between bg-zinc-900 p-6">
      <div />
      <div class="flex flex-col gap-8 items-center">
        <a
          href="https://ai-hub.bbv.ch"
          target="_blank"
          rel="noopener noreferrer"
        >
          <img
            :src="logo"
            alt="Logo of company"
            class="w-32 lg:w-32 rounded"
          >
        </a>
        <div class="flex flex-col gap-2 text-center">
          <h2 class="text-xl text-white">
            Willkommen im AI Hub von {{ companyName }}
          </h2>
          <p class="text-gray-400">
            Bitte loggen Sie sich ein
          </p>
        </div>
        <Button
          label="Login with Microsoft"
          icon="pi pi-microsoft"
          icon-pos="right"
          @click="login"
        />
      </div>
      <a
        href="https://bbv.ch/services/generative-ai/"
        target="_blank"
        rel="noopener noreferrer"
        class="text-gray-400 hidden sm:block"
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
