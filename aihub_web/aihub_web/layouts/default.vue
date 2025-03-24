<template>
  <div class="w-full flex flex-row bg-stone-50 dark:bg-stone-950">
    <div class="w-[50px] h-screen fixed flex flex-col items-center justify-between shadow-stone-500 shadow-md bg-white dark:bg-black">
      <div class="h-[50px] w-full flex items-center justify-center">
        <ServiceSelection />
      </div>
      <div class="flex flex-col justify-center gap-8">
        <nuxt-link-locale
          v-for="app in nonAdminApps"
          :key="app.path"
          :to="app.path"
          class="w-full h-[50px] flex items-center justify-center"
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
              class="w-[1.2rem] h-[1.7rem]"
            />
          </Button>
        </nuxt-link-locale>
      </div>
      <div>
        <UserSettings />
      </div>
    </div>
    <div class="pl-[50px] w-full">
      <div class="h-[50px] px-2 w-full flex justify-between items-center ">
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
                class="h-[50px] flex items-center justify-center"
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
        <div class="h-full flex items-center overflow-hidden">
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
import type { MenuItem } from 'primevue/menuitem'
import { useSuiteStore } from '@core/stores/useSuiteStore'
import logo from '../assets/images/logo.png'

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
