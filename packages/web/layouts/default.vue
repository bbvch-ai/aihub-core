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
      <div class="flex flex-col items-center">
        <SupportIncidentButton />
        <UserSettings />
      </div>
      <SupportIncidentDialog />
    </div>
    <div class="w-full pl-[50px]">
      <div class="fixed z-50 flex h-[50px] w-full items-center justify-between bg-surface-50 pr-[50px] dark:bg-surface-950">
        <Breadcrumb
          class="!bg-transparent text-xs opacity-70"
          :home="breadcrumbHome"
          :model="breadcrumbItems"
        >
          <template #item="{ item }">
            <NuxtLink
              v-if="item.route"
              :to="item.route"
              class="hover:underline"
            >
              {{ item.label }}
            </NuxtLink>
            <span v-else>{{ item.label }}</span>
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
const router = useRouter()
const tenantPath = useTenantPath()

// Here rather than app.vue: this layout is where the language switcher lives,
// and extenders supplying their own app.vue would otherwise lose the restore.
useRestorePreferredLocale()

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

const breadcrumbHome = computed<MenuItem>(() => ({ ...apps.value[0], route: tenantPath('/') }))

// `service` is only the URL prefix every page shares, not a page of its own.
const breadcrumbItems = computed<MenuItem[]>(() => {
  const segments = route.path.split('/').filter(Boolean).slice(2)
  const lastIndex = segments.length - 1
  return segments
    .map((segment: string, index: number) => {
      const appPath = '/' + segments.slice(0, index + 1).join('/')
      const path = tenantPath(appPath)
      const app = apps.value.find((candidate: MenuItem) => candidate.path === appPath)
      return {
        label: app?.label ?? segment,
        route: index < lastIndex && router.resolve(path).matched.length > 0 ? path : undefined,
      }
    })
    .filter((_item: MenuItem, index: number) => !(index === 0 && segments[0] === 'service'))
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
