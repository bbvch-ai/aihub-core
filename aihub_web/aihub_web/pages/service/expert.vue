<template>
  <StructuralScreen>
    <template #top>
      <div class="flex items-center gap-4">
        <h1 class="text-3xl">
          {{ t('expert.title') }}
        </h1>
        <SelectButton
          :model-value="activeNavItem"
          :options="navItems"
          data-key="key"
          option-label="name"
          size="small"
          @update:model-value="toNavItem"
        >
          <template #option="{ option }">
            <div class="flex items-center gap-2">
              <span>{{ option.name }}</span>
              <Badge
                v-if="option.key === 'questions' && pendingCount > 0"
                :value="pendingCount"
                severity="danger"
              />
            </div>
          </template>
        </SelectButton>
      </div>
    </template>
    <NuxtPage />
  </StructuralScreen>
</template>

<script setup lang="ts">
import { usePendingExpertQuestionsCount } from '@core/composables/expert/useExpertQuestions'
import { computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'

import type { NavItem } from '@core/types/NavItem'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const localePath = useLocalePath()

const { count: pendingCount } = usePendingExpertQuestionsCount()

const subPath = (path: string) => `/service/expert/${path}`

onMounted(() => {
  if (route.path === localePath('/service/expert')) {
    router.push(localePath(subPath('questions')))
  }
})

const isActive = (path: string) => {
  return () => {
    const localizedPath = localePath(subPath(path))
    return route.path.startsWith(localizedPath)
  }
}

const navItems = computed<NavItem[]>(() => [
  { name: t('expert.tabs.questions'), key: 'questions', path: subPath('questions'), isActive: isActive('questions') },
  { name: t('expert.tabs.groups'), key: 'groups', path: subPath('groups'), isActive: isActive('groups') },
])

const toNavItem = (navItem: NavItem) => {
  router.push(localePath(navItem.path))
}

const activeNavItem = computed<NavItem | undefined>(() => {
  return navItems.value.find(navItem => navItem.isActive())
})
</script>
