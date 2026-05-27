<template>
  <Button
    aria-label="Menu"
    variant="text"
    @click="toggle"
  >
    <template #icon>
      <Icon
        name="mage:dots-menu"
        size="xl"
      />
    </template>
  </Button>
  <Popover
    ref="op"
    class="[--p-popover-background:#f9f9f9] [--p-popover-border-color:#e3e3e3] dark:[--p-popover-background:#0d0d0d] dark:[--p-popover-border-color:#333]"
  >
    <div
      v-focustrap
      class="flex flex-col gap-4 p-5"
    >
      <div>
        <h2 class="text-xl">
          {{ t('service.selection.title') }}
        </h2>
        <p class="text-sm">
          {{ t('service.selection.description') }}
        </p>
      </div>
      <IconField>
        <InputIcon>
          <i class="pi pi-search" />
        </InputIcon>
        <InputText
          id="input"
          v-model="search"
          size="small"
          type="text"
          :placeholder="t('service.selection.search')"
          autofocus
          fluid
          @keydown.enter="onEnter"
        />
      </IconField>
    </div>
    <div class="relative grid grid-cols-4 gap-3 p-5">
      <template v-if="appsLoading">
        <skeleton
          v-for="i in 6"
          :key="i"
          width="5rem"
          height="5rem"
        />
      </template>
      <template
        v-else
      >
        <div
          v-for="app in shownApps"
          :key="app.path"
          :class="[
            'rounded-2xl border  p-3 transition-colors hover:border-primary-500 dark:border-primary-900  hover:dark:border-primary-400',
            isActiveApp(app.path)
              ? 'bg-surface-200 dark:bg-surface-800'
              : 'bg-surface-100 dark:bg-surface-900',
          ]"
        >
          <NuxtLink
            :to="app.path === '/' ? tenantPath('/') : tenantPath(app.path)"
            class="flex h-[50px] items-center justify-center"
            @click="toggle"
          >
            <div class="flex h-[60px] min-w-[80px] flex-col items-center justify-center gap-2">
              <Icon
                :name="app.icon"
                class="size-6"
              />
              <p
                :class="[
                  'text-sm font-medium',
                ]"
              >
                {{ app.label }}
              </p>
            </div>
          </NuxtLink>
        </div>
        <div
          v-for="i in 4"
          :key="i"
          class="px-3"
        >
          <div class="h-0 min-w-[80px]" />
        </div>
      </template>
    </div>
  </Popover>
</template>

<script setup lang="ts">
import type { MenuItem } from 'primevue/menuitem'

const router = useRouter()
const route = useRoute()
const tenantPath = useTenantPath()

const { apps, appsLoading } = useApps()
const { t } = useI18n()

const shownApps = computed(() => {
  return search.value
    ? apps.value.filter((app: MenuItem) => {
        const label = typeof app.label === 'string'
          ? app.label
          : ''
        return label.toLowerCase().includes(search.value.toLowerCase())
      })
    : apps.value
})

const isActiveApp = (appPath: string | undefined) => {
  if (!appPath) return false
  const localizedPath = tenantPath(appPath)
  // For home page, only match exact path
  if (appPath === '/') {
    return route.path === localizedPath
  }
  // For other pages, match exact or nested routes
  return route.path === localizedPath || route.path.startsWith(localizedPath + '/')
}

const search = ref('')
watch(() => route.path, () => {
  search.value = ''
})

const op = ref()
const toggle = (event: Event) => {
  op.value.toggle(event)
}

const onEnter = (event: Event) => {
  if (shownApps.value.length > 0) {
    router.push(tenantPath(shownApps.value[0].path))
    toggle(event)
  }
}
</script>
