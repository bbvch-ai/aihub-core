<template>
  <StructuralScreen>
    <StructuralColumn
      :title="t('role.title')"
      :loading="rolesAreLoading"
    >
      <div class="grid grid-cols-2 gap-4 2xl:grid-cols-2">
        <RoleCard
          v-for="role in roles"
          :key="role.id"
          :role="role"
          @click="() => toRole(role)"
        />
      </div>
    </StructuralColumn>
    <NuxtPage />
  </StructuralScreen>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import type { RoleResponse } from '@core/sdk/client'

import { useLocalePath } from '#i18n'

const router = useRouter()
const localePath = useLocalePath()
const { t } = useI18n()

const { roles, rolesAreLoading } = useRoles()

const toRole = (role: RoleResponse) => {
  router.push(localePath(`/service/role/${role.id}`))
}
</script>

<style scoped>

</style>
