<template>
  <StructuralScreen>
    <StructuralColumn
      :title="t('agent.title')"
      :loading="isLoading"
    >
      <Tabs
        v-model:value="activeTab"
      >
        <TabList>
          <Tab value="agents">
            {{ t('agent.tabs.myAgents') }}
          </Tab>
          <Tab value="templates">
            {{ t('agent.tabs.templates') }}
          </Tab>
        </TabList>
        <TabPanels>
          <TabPanel value="agents">
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
          </TabPanel>
          <TabPanel value="templates">
            <div class="flex flex-col gap-12 pt-4">
              <div
                v-for="group in groupedTemplates"
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
                  <AgentTemplateCard
                    v-for="(tmpl, index) in group.templates"
                    :key="`${group.agentClass}-${index}`"
                    :template="tmpl"
                    :agent-class-name="group.name"
                    :locale="locale"
                    @click="openCreateModalWithTemplate(group.agentClass, index)"
                  />
                </div>
              </div>
              <div
                v-if="groupedTemplates.length === 0"
                class="flex flex-col items-center justify-center py-12 text-center"
              >
                <p class="text-sm text-surface-500">
                  {{ t('agent.templates.empty') }}
                </p>
              </div>
            </div>
          </TabPanel>
        </TabPanels>
      </Tabs>
      <AgentCreateModal
        v-model="createModalOpen"
        :initial-class="selectedClassForCreate"
        :initial-template="selectedTemplateForCreate"
        @success="handleCreateSuccess"
      />
    </StructuralColumn>

    <NuxtPage />
  </StructuralScreen>
</template>

<script setup lang="ts">
import type { FullAgentInstanceDto } from '@core/sdk/client'

import { useLocalePath } from '#i18n'

const router = useRouter()
const localePath = useLocalePath()
const { t, locale } = useI18n()

const { agentInstances, agentInstancesAreLoading } = useAgentInstances()
const { agentClasses, agentClassesAreLoading } = useAgentClasses()

const isLoading = computed(() => agentInstancesAreLoading.value || agentClassesAreLoading.value)

const activeTab = ref<'agents' | 'templates'>('agents')

const createModalOpen = ref(false)
const selectedClassForCreate = ref('')
const selectedTemplateForCreate = ref<number | null>(null)

const openCreateModal = (agentClass: string) => {
  selectedClassForCreate.value = agentClass
  selectedTemplateForCreate.value = null
  createModalOpen.value = true
}

const openCreateModalWithTemplate = (agentClass: string, templateIndex: number) => {
  selectedClassForCreate.value = agentClass
  selectedTemplateForCreate.value = templateIndex
  createModalOpen.value = true
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
        // Class not available - create group but mark as unavailable
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

const groupedTemplates = computed(() => {
  if (!agentClasses.value) return []

  const localeKey = locale.value as 'de' | 'en' | 'fr' | 'it'

  return agentClasses.value
    .filter(classInfo => classInfo.templates && classInfo.templates.length > 0)
    .map(classInfo => ({
      agentClass: classInfo.agent_class,
      name: classInfo.name?.[localeKey] ?? classInfo.agent_class,
      description: classInfo.description?.[localeKey] ?? '',
      icon: classInfo.icon ?? 'meteor-icons:robot',
      templates: classInfo.templates!,
    }))
    .sort((a, b) => a.agentClass.localeCompare(b.agentClass))
})

const toAgent = (agent: FullAgentInstanceDto) => {
  router.push(localePath(`/service/agents/${agent.agent_class}-${agent.agent_id}/overview`))
}

const handleCreateSuccess = (agentClass: string, agentId: string) => {
  // Navigate to the newly created agent
  router.push(localePath(`/service/agents/${agentClass}-${agentId}/overview`))
}
</script>
