<template>
  <NuxtLayout>
    <NuxtPage />
    <Toast />
    <ConfirmDialog />
  </NuxtLayout>
</template>

<script setup lang="ts">
import 'primeicons/primeicons.css'
import 'gridstack/dist/gridstack.min.css'
import { client } from './sdk/client/client.gen'

const { getToken } = useAuth()
const { t, locale, setLocale } = useI18n()
const localePath = useLocalePath()
const switchLocalePath = useSwitchLocalePath()
const router = useRouter()
const route = useRoute()
const toast = useToast()
useNotificationPoller()

const { myUser } = useMyUser()
const { updateMyLocale } = useUpdateMyLocale()
const localeBootstrapped = ref(false)
watch(myUser, (user) => {
  if (!user || localeBootstrapped.value) return
  localeBootstrapped.value = true
  const persisted = (user as { preferred_locale?: string | null }).preferred_locale
  if (persisted && persisted !== locale.value) {
    setLocale(persisted as never)
    const target = switchLocalePath(persisted)
    if (target) router.replace(target)
  }
  else if (!persisted) {
    updateMyLocale({ locale: locale.value }).catch((err) => {
      console.error('Failed to bootstrap user locale', err)
    })
  }
}, { immediate: true })
client.setConfig({
  baseURL: '/api/v1',
  auth: async () => {
    return await getToken()
  },
  onRequest: ({ options }) => {
    options.headers.set('lang', locale.value)
  },
  onResponseError: async ({ response }) => {
    console.error('API error', response.status, response._data?.detail)

    // Invalid or inaccessible tenant → redirect to tenant selection
    if (response.status === 403 && response._data?.detail === 'Access denied') {
      await navigateTo(localePath('/select-tenant'), { replace: true })
      return
    }

    // Suppress error toasts on pages without tenant context (login, select-tenant, callback)
    if (!route.params.tenant) return

    const rawDetail = response._data?.detail
    const message = typeof rawDetail === 'object' && rawDetail?.message
      ? rawDetail.message
      : rawDetail
    toast.add({
      severity: 'error',
      summary: t(`http_error.code.${response.status}`),
      detail: message,
      life: 10_000,
    })
  },
})
</script>
