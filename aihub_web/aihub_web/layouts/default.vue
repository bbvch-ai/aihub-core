<template>
  <div class="w-full flex flex-row">
    <div class="w-[50px] h-screen flex flex-col items-center justify-between shadow-gray-500 shadow-md">
      <div class="h-[50px] w-full flex items-center justify-center">
        <Button
          aria-label="Menu"
          variant="text"
          @click="toggle"
        >
          <template #icon>
            <Icon
              name="bi:stack"
              size="xl"
            />
          </template>
        </Button>
        <Popover ref="op">
          <div v-focustrap>
            <IconField>
              <InputIcon>
                <i class="pi pi-search" />
              </InputIcon>
              <InputText
                id="input"
                v-model="search"
                size="small"
                type="text"
                placeholder="Search"
                autofocus
                fluid
                @keydown.enter="onEnter"
              />
            </IconField>
          </div>
          <div class="flex p-5 gap-7 max-w-[430px] flex-wrap relative mt-5">
            <nuxt-link-locale
              v-for="app in shownApps"
              :key="app.path"
              :to="app.path"
              class="h-[50px] flex items-center justify-center"
              @click="toggle"
            >
              <div class="w-[80px] h-[60px]  flex flex-col gap-2 justify-center items-center ">
                <span
                  :class="app.icon"
                  class="text-xl"
                />
                <p>{{ app.label }}</p>
              </div>
            </nuxt-link-locale>
          </div>
        </Popover>
      </div>
      <div class="flex flex-col justify-center gap-8">
        <nuxt-link-locale
          v-for="app in favoriteApps"
          :key="app.path"
          :to="app.path"
          class="w-full h-[50px] flex items-center justify-center"
        >
          <Button
            rounded
            :icon="app.icon"
            :aria-label="app.label"
            :variant="appIsActive(app) ? undefined : 'text'"
            size="large"
          />
        </nuxt-link-locale>
      </div>
      <div>
        <nuxt-link-locale
          to="/settings"
          class="w-full h-[50px] flex items-center justify-center"
        >
          <Button
            icon="pi pi-cog"
            aria-label="Settings"
            variant="text"
            size="large"
            disabled
          />
        </nuxt-link-locale>
      </div>
    </div>
    <div class="w-full">
      <div class="h-[50px] px-2 w-full flex justify-between items-center">
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
import logo from '../assets/images/logo.png'

const localeRoute = useLocaleRoute()
const router = useRouter()
const route = useRoute()

const search = ref('')
watch(() => route.path, () => search.value = '')

const apps = reactive<MenuItem>([
  { icon: 'pi pi-home', label: 'Hub', path: '/' },
  { icon: 'pi pi-comments', label: 'Chat UI', path: '/module/webui' },
])
const shownApps = computed(() => {
  return search.value ? apps.filter(app => app.label.toLowerCase().includes(search.value.toLowerCase())) : apps
})

const favorites = reactive([
  'Hub',
  'Chat UI',
])

const favoriteApps = computed(() => {
  return apps.filter((app: MenuItem) => favorites.includes(app.label))
})

const appIsActive = (app: MenuItem) => {
  return route.path === localeRoute(app.path)?.path
}

const activeApp = computed(() => {
  return apps.find((app: MenuItem) => appIsActive(app))
})

const breadcrumbItems = computed(() => {
  if (!activeApp.value || activeApp.value.path == '/') return []
  return [activeApp.value]
})

const op = ref()
const toggle = (event) => {
  op.value.toggle(event)
}

const onEnter = (event) => {
  if (shownApps.value.length > 0) {
    router.push(localeRoute(shownApps.value[0].path))
    toggle(event)
  }
}
</script>

<style scoped>

</style>
