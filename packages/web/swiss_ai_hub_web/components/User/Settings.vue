<template>
  <Button
    icon="pi pi-cog"
    aria-label="Settings"
    variant="text"
    size="large"
    @click="toggle"
  />
  <Popover
    ref="op"
    class="[--p-popover-background:var(--p-surface-50)] [--p-popover-border-color:var(--p-surface-200)] dark:[--p-popover-background:var(--p-surface-950)] dark:[--p-popover-border-color:var(--p-surface-800)]"
  >
    <div class="flex flex-col gap-4 p-2">
      <div class="flex flex-col gap-2">
        <label class="font-medium">{{ t('user.language') }}</label>
        <Select
          v-model="selectedLocale"
          :options="localeOptions"
          option-label="name"
          class="w-full"
        />
      </div>
      <Button
        class="w-full"
        :label="t('user.logout')"
        variant="text"
        icon="pi pi-arrow-circle-right"
        icon-pos="right"
        @click="auth.logout"
      />
    </div>
  </Popover>
</template>

<script setup lang="ts">
import { changeLocale } from '@formkit/vue'
import { useQueryCache } from '@pinia/colada'

const auth = useAuth()
const { t, locale, locales } = useI18n()
const queryCache = useQueryCache()
const switchLocalePath = useSwitchLocalePath()
const router = useRouter()
const { updateMyLocale } = useUpdateMyLocale()

const op = ref()
const toggle = (event: Event) => {
  op.value.toggle(event)
}

// Format locales for the Select component
const localeOptions = computed(() => {
  return locales.value.map(l => ({
    code: l.code,
    name: l.name,
  }))
})

changeLocale(locale.value)

// Track the selected locale
const selectedLocale = computed({
  get: () => {
    return localeOptions.value.find(l => l.code === locale.value) || localeOptions.value[0]
  },
  set: (newValue) => {
    if (newValue?.code && newValue.code !== locale.value) {
      op.value.hide()
      changeLocale(newValue.code)
      updateMyLocale({ locale: newValue.code }).catch((err) => {
        console.error('Failed to persist user locale', err)
      })
      router.push(switchLocalePath(newValue.code))
        .then(() => {
          queryCache.invalidateQueries()
        })
    }
  },
})
</script>
