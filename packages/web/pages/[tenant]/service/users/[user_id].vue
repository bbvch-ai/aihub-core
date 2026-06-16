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
              {{ t('user.list.sys_admin') }}
            </span>
            <Tag
              v-if="user.is_sys_admin"
              :value="t('user.list.sys_admin_tag')"
              severity="success"
              icon="pi pi-crown"
            />
            <Tag
              v-else
              :value="t('user.list.sys_admin_no')"
              severity="secondary"
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
      <AccessCapabilities
        :rules="user.access_rules"
        readonly
      />
    </div>
  </StructuralColumn>
</template>

<script setup lang="ts">
import AccessCapabilities from '@/components/Role/AccessCapabilities.vue'

const { user, userIsLoading } = useUser()
const { t } = useI18n()
</script>

<style scoped>
.panel :deep(.p-panel-header) {
  padding: 0 !important;
}
</style>
