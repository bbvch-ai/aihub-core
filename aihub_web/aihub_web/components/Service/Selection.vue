<template>
  <Button
    aria-label="Menu"
    variant="text"
    @click="toggle"
  >
    <template #icon>
      <Icon
        name="akar-icons:dot-grid"
        size="xl"
      />
    </template>
  </Button>
  <Popover
    ref="op"
    class="bg-white dark:bg-stone-900"
  >
    <div
      v-focustrap
      class="flex flex-col gap-4 p-5"
    >
      <div>
        <h2 class="text-xl">
          Services
        </h2>
        <p class="text-sm">
          Here are all the services listed that you have activated
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
          placeholder="Search"
          autofocus
          fluid
          @keydown.enter="onEnter"
        />
      </IconField>
    </div>
    <div class="relative flex max-w-[460px] flex-wrap gap-10 p-5">
      <template v-if="loadingSuite !== 'success'">
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
        <nuxt-link-locale
          v-for="app in shownApps"
          :key="app.path"
          :to="app.path"
          class="flex h-[50px] items-center justify-center"
          @click="toggle"
        >
          <div class="flex h-[60px]  w-[80px] flex-col items-center justify-center gap-2 ">
            <Icon
              :name="app.icon"
              style="color: #9c9c9c"
              class="size-8"
            />
            <p>
              {{ app.label }}
            </p>
          </div>
        </nuxt-link-locale>
      </template>
    </div>
  </Popover>
</template>

<script setup lang="ts">
import { useSuiteStore } from '@core/stores/useSuiteStore'

import type { MenuItem } from 'primevue/menuitem'

const router = useRouter()
const localeRoute = useLocaleRoute()
const route = useRoute()

const { loadingSuite, apps } = storeToRefs(useSuiteStore())

const shownApps = computed(() => {
  return search.value ? apps.value.filter((app: MenuItem) => app.label?.toLowerCase().includes(search.value.toLowerCase())) : apps.value
})

const search = ref('')
watch(() => route.path, () => search.value = '')

const op = ref()
const toggle = (event: Event) => {
  op.value.toggle(event)
}

const onEnter = (event: Event) => {
  if (shownApps.value.length > 0) {
    router.push(localeRoute(shownApps.value[0].path))
    toggle(event)
  }
}
</script>

<style scoped>

</style>
