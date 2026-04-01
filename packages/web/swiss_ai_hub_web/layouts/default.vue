<template>
  <div class="flex min-h-screen w-full flex-row bg-white dark:bg-surface-900">
    <div class="fixed flex h-screen w-[50px] flex-col items-center justify-between bg-surface-50 dark:bg-surface-950">
      <div class="flex h-[50px] w-full items-center justify-center">
        <ServiceSelection />
      </div>
      <div class="flex flex-col justify-center gap-2">
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
      <div class="fixed z-50 flex h-[50px] w-full items-center justify-between bg-surface-50 pr-[50px] dark:bg-surface-950">
        <Breadcrumb
          class="!bg-transparent text-xs opacity-70"
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
      <div class="h-[50px] w-full" />
      <div v-if="online">
        <slot />
      </div>
      <div
        v-else
        class="flex h-screen w-full items-center justify-center"
      >
        <div
          class="loader relative aspect-square w-[64px]"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import logo from '@core/assets/images/logo.png'
import { getHealth } from '@core/sdk/client'

import type { MenuItem } from 'primevue/menuitem'

const route = useRoute()
const localePath = useLocalePath()

const online = ref<boolean>(false)

const { apps } = useApps()

const nonAdminApps = computed<MenuItem>(() => {
  return apps.value.filter((app: MenuItem) => !app.isAdmin)
})

const appIsActive = (app: MenuItem) => {
  const localizedPath = localePath(app.path)
  if (app.path === '/') {
    return route.path === localizedPath
  }
  return route.path.startsWith(localizedPath)
}

const breadcrumbItems = computed(() => {
  const paths = route.path.split('/').filter(Boolean).slice(1)
  return paths.map((label: string) => ({ label }))
})

getHealth({
  composable: '$fetch',
  baseURL: '/api/v1',
})
  .then((response) => {
    online.value = response.code == 200
  })
  .catch(() => {
    online.value = false
  })
</script>

<style scoped>
.loader:before,
.loader:after {
  content: "";
  position: absolute;
  border-radius: 50px;
  box-shadow: 0 0 0 3px inset #808080;
  animation: l4 2.5s infinite;
}
.loader:after {
  animation-delay: -1.25s;
}
@keyframes l4 {
  0% {
    inset: 0 35px 35px 0;
  }
  12.5% {
    inset: 0 35px 0 0;
  }
  25% {
    inset: 35px 35px 0 0;
  }
  37.5% {
    inset: 35px 0 0 0;
  }
  50% {
    inset: 35px 0 0 35px;
  }
  62.5% {
    inset: 0 0 0 35px;
  }
  75% {
    inset: 0 0 35px 35px;
  }
  87.5% {
    inset: 0 0 35px 0;
  }
  100% {
    inset: 0 35px 35px 0;
  }
}
</style>
