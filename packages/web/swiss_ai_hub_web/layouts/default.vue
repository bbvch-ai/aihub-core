<template>
  <div class="flex min-h-screen w-full flex-row bg-white dark:bg-surface-900">
    <div class="fixed flex h-screen w-[50px] flex-col items-center justify-between bg-surface-50 dark:bg-surface-950">
      <div class="flex h-[50px] w-full items-center justify-center">
        <ServiceSelection />
      </div>
      <div class="flex flex-col justify-center gap-2">
        <NuxtLink
          v-for="app in nonAdminApps"
          :key="app.path"
          :to="app.path === '/' ? tenantPath('/') : tenantPath(app.path)"
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
        </NuxtLink>
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
            <NuxtLink
              :to="item.route"
              class="hover:underline"
            >
              {{ item.label }}
            </NuxtLink>
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
        <AppLoader />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import logo from '@core/assets/images/logo.png'
import { getHealth } from '@core/sdk/client'

import type { MenuItem } from 'primevue/menuitem'

const route = useRoute()
const tenantPath = useTenantPath()

const online = ref<boolean>(false)

const { apps } = useApps()

const nonAdminApps = computed<MenuItem>(() => {
  return apps.value.filter((app: MenuItem) => !app.isAdmin)
})

const appIsActive = (app: MenuItem) => {
  const resolvedPath = app.path === '/' ? tenantPath('/') : tenantPath(app.path)
  if (app.path === '/') {
    return route.path === resolvedPath
  }
  return route.path.startsWith(resolvedPath)
}

const breadcrumbItems = computed(() => {
  const segments = route.path.split('/').filter(Boolean)
  const prefixSegments = segments.slice(0, 2)
  const contentSegments = segments.slice(2)
  return contentSegments.map((label: string, index: number) => ({
    label,
    route: '/' + [...prefixSegments, ...contentSegments.slice(0, index + 1)].join('/'),
  }))
})

try {
  const response = await getHealth({
    composable: '$fetch',
    baseURL: '/api/v1',
  })
  online.value = response.code == 200
}
catch {
  online.value = false
}
</script>
