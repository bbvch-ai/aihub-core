<template>
  <StructuralColumn
    :title="user?.name"
    close-route="/service/users"
    :loading="userIsLoading"
  >
    <div class="flex flex-col gap-12">
      <Panel
        class="panel pt-5"
      >
        <div class="grid grid-cols-2 gap-4 xl:grid-cols-4">
          <div class="flex flex-col items-start gap-2">
            <span class="font-semibold">
              {{ t('user.list.name') }}
            </span>
            <Tag
              :value="user.name"
              severity="secondary"
            />
          </div>
          <div class="flex flex-col items-start gap-2">
            <span class="font-semibold">
              {{ t('user.list.email') }}
            </span>
            <Tag
              :value="user.email"
              severity="secondary"
            />
          </div>
          <div class="flex flex-col items-start gap-2">
            <span class="font-semibold">
              {{ t('user.list.last_accessed') }}
            </span>
            <Tag
              v-if="user.last_accessed"
              :value="getTimeAgo(user.last_accessed).text"
              :severity="getTimeAgo(user.last_accessed).severity"
            />
          </div>
          <div class="flex flex-col items-start gap-2">
            <span class="font-semibold">
              {{ t('user.list.roles') }}
            </span>
            <div class="flex flex-wrap gap-2">
              <Badge
                v-for="role in user.roles"
                :key="role"
                :value="role"
              />
            </div>
          </div>
        </div>
      </Panel>
      <div class="flex flex-col gap-8">
        <div class="flex flex-col gap-3">
          <h3 class="text-2xl">
            Services
          </h3>
          <div class="flex flex-wrap gap-2">
            <Tag
              v-for="service in user.access.services"
              :key="service.name"
              v-tooltip.top="service.level === 2 ? 'Admin' : 'User'"
              :value="service.name"
              :icon="service.level === 2 ? 'pi pi-crown' : undefined"
            />
          </div>
        </div>
        <div class="flex flex-col gap-3">
          <h3 class="text-2xl">
            Agents
          </h3>
          <div class="flex flex-wrap gap-2">
            <Tag
              v-for="agent in user.access.agents"
              :key="agent.name"
              v-tooltip.top="agent.level === 2 ? 'Admin' : 'User'"
              :value="agent.name"
              :icon="agent.level === 2 ? 'pi pi-crown' : undefined"
            />
          </div>
        </div>
        <div class="flex flex-col gap-3">
          <h3 class="text-2xl">
            {{ t('process.title') }}
          </h3>
          <div class="flex flex-wrap gap-2">
            <Tag
              v-for="process in user.access.processes"
              :key="process.name"
              v-tooltip.top="process.level === 2 ? 'Admin' : 'User'"
              :value="process.name"
              :icon="process.level === 2 ? 'pi pi-crown' : undefined"
            />
          </div>
        </div>
      </div>
    </div>
  </StructuralColumn>
</template>

<script setup lang="ts">
const { user, userIsLoading } = useUser()
const { t } = useI18n()
const { getTimeAgo } = useTimeAgo()
</script>

<style scoped>
.panel :deep(.p-panel-header) {
  padding: 0 !important;
}
</style>
