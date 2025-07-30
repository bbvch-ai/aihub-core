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
    class="bg-surface-50 text-black dark:bg-surface-950 dark:text-white"
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
    <div class="relative flex w-[500px] grow flex-wrap justify-between gap-3 p-5">
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
          class="rounded-2xl border p-3 hover:bg-surface-500/5 dark:border-surface-700"
        >
          <nuxt-link-locale
            :to="app.path"
            class="flex h-[50px] items-center justify-center"
            @click="toggle"
          >
            <div class="flex h-[60px] min-w-[80px] flex-col items-center justify-center gap-2 ">
              <Icon
                :name="app.icon"
                style="color: #9c9c9c"
                class="size-6"
              />
              <p class="text-sm font-medium">
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

const { apps, appsLoading } = useApps()
const { t } = useI18n()

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
