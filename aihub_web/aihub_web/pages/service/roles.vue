<template>
  <StructuralScreen>
    <StructuralColumn
      :title="t('role.title')"
      :loading="rolesAreLoading"
    >
      <div class="flex flex-col gap-2">
        <div class="flex w-full justify-end">
          <Button
            :label="t('role.create_new')"
            icon="pi pi-plus"
            @click="createModalOpen = true"
          />
          <Dialog
            v-model:visible="createModalOpen"
            modal
            :header="t('role.create_new')"
          >
            <RoleCreate
              @close="createModalOpen = false"
            />
          </Dialog>
        </div>
        <div class="grid grid-cols-2 gap-4 2xl:grid-cols-2">
          <RoleCard
            v-for="role in roles"
            :key="role.id"
            :role="role"
            @click="() => toRole(role)"
          />
        </div>
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

const createModalOpen = ref(false)

const toRole = (role: RoleResponse) => {
  router.push(localePath(`/service/roles/${role.id}`))
}
</script>

<style scoped>

</style>
