<template>
  <div v-if="isAgentAdmin">
    <h1 class="w-full pb-32 pt-72 text-center text-6xl">
      {{ t('welcome') }}
    </h1>
    <DashboardGrid />
  </div>
</template>

<script setup lang="ts">
const { t } = useI18n()
const { myUser, myUserIsLoading } = useMyUser()
const tenantPath = useTenantPath()

const ACCESS_LEVEL_ADMIN = 2

const isAgentAdmin = computed(() => {
  const agents = myUser.value?.access?.agents ?? []
  return agents.some(agent => agent.level === ACCESS_LEVEL_ADMIN)
})

watch(
  [myUserIsLoading, isAgentAdmin],
  ([isLoading, isAdmin]) => {
    if (!isLoading && !isAdmin) {
      navigateTo(tenantPath('/service/openai'), { replace: true })
    }
  },
  { immediate: true },
)
</script>
