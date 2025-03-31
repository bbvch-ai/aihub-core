<template>
  <div class="flex min-h-screen w-full flex-row bg-surface-50 dark:bg-surface-950">
    <div class="fixed flex h-screen w-[50px] flex-col items-center justify-between bg-white shadow-md shadow-surface-500 dark:bg-surface-900">
      <div class="flex h-[50px] w-full items-center justify-center">
        <ServiceSelection />
      </div>
      <div class="flex flex-col justify-center gap-8">
        <nuxt-link-locale
          v-for="app in nonAdminApps"
          :key="app.path"
          :to="app.path"
          class="flex h-[50px] w-full items-center justify-center"
        >
          <Button
            v-tooltip="{ value: app.label, showDelay: 0 }"
            rounded
            :aria-label="app.label"
            :variant="appIsActive(app) ? undefined : 'text'"
            size="large"
          >
            <Icon
              :name="app.icon"
              class="h-[1.7rem] w-[1.2rem]"
            />
          </Button>
        </nuxt-link-locale>
      </div>
      <div>
        <UserSettings />
      </div>
    </div>
    <div class="w-full pl-[50px]">
      <div class="flex h-[50px] w-full items-center justify-between px-2 ">
        <Breadcrumb
          class="!bg-transparent"
          :home="apps[0]"
          :model="breadcrumbItems"
        >
          <template #item="{ item }">
            <a
              class="cursor-pointer"
              :href="item.url"
            >
              <nuxt-link-locale
                :to="item.path"
                class="flex h-[50px] items-center justify-center"
              >
                <span>{{ item.label }}</span>
              </nuxt-link-locale>
            </a>
          </template>
        </Breadcrumb>
        <img
          :src="logo"
          alt="AI Hub"
          class="h-[25px]"
        >
        <div class="flex h-full items-center overflow-hidden">
          <UserBar />
        </div>
      </div>
      <div>
        <slot />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useSuiteStore } from '@core/stores/useSuiteStore'

import logo from '../assets/images/logo.png'

import type { MenuItem } from 'primevue/menuitem'

const route = useRoute()
const localeRoute = useLocaleRoute()

const { apps } = storeToRefs(useSuiteStore())

const nonAdminApps = computed<MenuItem>(() => {
  return apps.value.filter((app: MenuItem) => !app.path.includes('/admin/'))
})

const appIsActive = (app: MenuItem) => {
  return route.path === localeRoute(app.path)?.path
}

const activeApp = computed(() => {
  return apps.value.find((app: MenuItem) => appIsActive(app))
})

const breadcrumbItems = computed(() => {
  if (!activeApp.value || activeApp.value.path == '/') return []
  return [activeApp.value]
})
</script>

<style scoped>

</style>
