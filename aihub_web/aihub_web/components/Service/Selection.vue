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
  <Popover ref="op">
    <div
      v-focustrap
      class="p-5 flex flex-col gap-4"
    >
      <h2 class="text-xl">
        Services
      </h2>
      <p>Here are all the services listed that you have activated</p>
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
    <div class="flex p-5 gap-10 max-w-[460px] flex-wrap relative">
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
          class="h-[50px] flex items-center justify-center"
          @click="toggle"
        >
          <div class="w-[80px] h-[60px]  flex flex-col gap-2 justify-center items-center ">
            <Icon
              :name="app.icon"
              style="color: #9c9c9c"
              class="w-[2rem] h-[2rem]"
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
import type { MenuItem } from 'primevue/menuitem'
import { useSuiteStore } from '@core/stores/useSuiteStore'

const router = useRouter()
const localeRoute = useLocaleRoute()
const route = useRoute()

const { loadingSuite, apps } = storeToRefs(useSuiteStore())

const shownApps = computed(() => {
  return search.value ? apps.value.filter((app: MenuItem) => app.value.label?.toLowerCase().includes(search.value.toLowerCase())) : apps.value
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
