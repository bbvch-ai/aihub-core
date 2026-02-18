<template>
  <StructuralScreen>
    <StructuralColumn
      :title="t('agent.title')"
      :loading="isLoading"
    >
      <SelectButton
        :model-value="activeNavItem"
        :options="navItems"
        data-key="key"
        option-label="name"
        size="small"
        @update:model-value="toNavItem"
      />
      <div class="flex flex-col gap-12 pt-4">
        <div
          v-for="group in groupedAgents"
          :key="group.agentClass"
        >
          <div class="pb-4">
            <div class="flex items-center gap-2 pb-2">
              <Icon
                :name="group.icon"
                size="2em"
                class="text-surface-500"
              />
              <span class="text-lg font-medium">{{ group.name }}</span>
            </div>
            <span
              v-if="group.description"
              class="pb-2 text-xs text-surface-500"
            >
              {{ group.description }}
            </span>
          </div>
          <div class="grid grid-cols-2 gap-4 2xl:grid-cols-2">
            <AgentCard
              v-for="agent in group.instances"
              :key="`${agent.agent_class}-${agent.agent_id}`"
              :agent="agent"
              @click="() => toAgent(agent)"
            />
            <AgentEmptyCard
              v-if="group.isAvailable"
              @add="openCreateModal(group.agentClass)"
            />
          </div>
        </div>
      </div>
      <AgentCreateModal
        v-model="createModalOpen"
        :initial-class="selectedClassForCreate"
        @success="handleCreateSuccess"
      />
    </StructuralColumn>

    <NuxtPage />
  </StructuralScreen>
</template>

<script setup lang="ts">
import type { FullAgentInstanceDto } from '@core/sdk/client'
import type { NavItem } from '@core/types/NavItem'

import { useLocalePath } from '#i18n'

const router = useRouter()
const route = useRoute()
const localePath = useLocalePath()
const { t, locale } = useI18n()

const { agentInstances, agentInstancesAreLoading } = useAgentInstances()
const { agentClasses, agentClassesAreLoading } = useAgentClasses()

const isLoading = computed(() => agentInstancesAreLoading.value || agentClassesAreLoading.value)

const createModalOpen = ref(false)
const selectedClassForCreate = ref('')

const openCreateModal = (agentClass: string) => {
  selectedClassForCreate.value = agentClass
  createModalOpen.value = true
}

const navItems = computed<NavItem[]>(() => [
  {
    name: t('agent.tabs.myAgents'),
    key: 'agents',
    path: '/service/agents',
    isActive: () => route.path.startsWith(localePath('/service/agents')),
  },
  {
    name: t('agent.tabs.templates'),
    key: 'templates',
    path: '/service/agent-templates',
    isActive: () => route.path.startsWith(localePath('/service/agent-templates')),
  },
])

const activeNavItem = computed<NavItem | undefined>(() => {
  return navItems.value.filter(navItem => navItem.isActive())[0]
})

const toNavItem = (navItem: NavItem | null) => {
  if (navItem) {
    router.push(localePath(navItem.path))
  }
}

const groupedAgents = computed(() => {
  const groups = new Map<string, {
    agentClass: string
    name: string
    description: string
    icon: string
    instances: FullAgentInstanceDto[]
    isAvailable: boolean
  }>()

  const localeKey = locale.value as 'de' | 'en' | 'fr' | 'it'

  // First, add all available agent classes (even those without instances)
  if (agentClasses.value) {
    for (const classInfo of agentClasses.value) {
      groups.set(classInfo.agent_class, {
        agentClass: classInfo.agent_class,
        name: classInfo.name?.[localeKey] ?? classInfo.agent_class,
        description: classInfo.description?.[localeKey] ?? '',
        icon: classInfo.icon ?? 'meteor-icons:robot',
        instances: [],
        isAvailable: true,
      })
    }
  }

  // Then, add instances to their groups (or create groups for unavailable classes)
  if (agentInstances.value) {
    for (const agent of agentInstances.value) {
      const existing = groups.get(agent.agent_class)
      if (existing) {
        existing.instances.push(agent)
      }
      else {
        groups.set(agent.agent_class, {
          agentClass: agent.agent_class,
          name: agent.agent_class,
          description: '',
          icon: 'meteor-icons:robot',
          instances: [agent],
          isAvailable: false,
        })
      }
    }
  }

  return Array.from(groups.values())
    .sort((a, b) => a.agentClass.localeCompare(b.agentClass))
})

const toAgent = (agent: FullAgentInstanceDto) => {
  router.push(localePath(`/service/agents/${agent.agent_class}-${agent.agent_id}/overview`))
}

const handleCreateSuccess = (agentClass: string, agentId: string) => {
  router.push(localePath(`/service/agents/${agentClass}-${agentId}/overview`))
}
</script>
