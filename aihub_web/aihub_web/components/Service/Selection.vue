<template>
  <Button
    aria-label="Menu"
    variant="text"
    @click="toggle"
  >
    <template #icon>
      <Icon
        name="mage:layout-grid"
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
            'rounded-2xl border p-3 transition-colors',
            isActiveApp(app.path)
              ? 'border-primary-500 bg-primary-500/10 dark:border-primary-400 dark:bg-primary-400/10'
              : 'hover:bg-surface-500/5 dark:border-surface-700',
          ]"
        >
          <nuxt-link-locale
            :to="app.path"
            class="flex h-[50px] items-center justify-center"
            @click="toggle"
          >
            <div class="flex h-[60px] min-w-[80px] flex-col items-center justify-center gap-2 ">
              <Icon
                :name="app.icon"
                :style="isActiveApp(app.path) ? 'color: var(--p-primary-500)' : 'color: #9c9c9c'"
                class="size-6"
              />
              <p
                :class="[
                  'text-sm font-medium',
                  isActiveApp(app.path) ? 'text-primary-500 dark:text-primary-400' : '',
                ]"
              >
                {{ app.label }}
              </p>
            </div>
          </nuxt-link-locale>
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
const localeRoute = useLocaleRoute()
const route = useRoute()
const localePath = useLocalePath()

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
  const localizedPath = localePath(appPath)
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
    const firstAppRoute = localeRoute(shownApps.value[0].path)
    if (firstAppRoute) {
      router.push(firstAppRoute)
      toggle(event)
    }
  }
}
</script>
