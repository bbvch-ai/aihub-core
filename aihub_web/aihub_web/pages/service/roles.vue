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
        <div
          class="flex min-h-full cursor-pointer flex-col justify-center gap-3 rounded-xl border-2 border-dashed border-surface-300 p-4 hover:border-primary-500 hover:bg-surface-50 dark:border-surface-600 dark:hover:bg-surface-800"
          @click="createModalOpen = true"
        >
          <div class="flex items-center justify-center">
            <div class="flex items-center justify-center p-3">
              <i
                class="pi pi-plus text-surface-400"
                style="font-size: 1.5rem"
              />
            </div>
          </div>
          <div class="text-center">
            <h3 class="font-medium text-surface-600 dark:text-surface-400">
              {{ t('role.create_new') }}
            </h3>
          </div>
        </div>
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
