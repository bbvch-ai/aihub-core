<template>
  <StructuralScreen>
    <StructuralColumn v-if="!isTemplatesRoute" :title="t('agent.title')" :loading="isLoading" size="large">
      <div class="flex justify-between">
        <SelectButton :model-value="activeNavItem" :options="navItems" data-key="key" option-label="name" size="small"
          @update:model-value="toNavItem" />
        <div class="flex items-center gap-4">
          <Select v-model="agentClass" :options="agentClassOptions" option-label="label" option-value="value"
            :placeholder="t('agent.list.filter.type_placeholder')" show-clear class="w-52" />
          <Select v-model="status" :options="statusOptions" option-label="label" option-value="value"
            :placeholder="t('agent.list.filter.status_placeholder')" show-clear class="w-52" />
          <InputText v-model="searchQuery" :placeholder="t('agent.list.search_placeholder')" class="w-80" />
        </div>
      </div>
      <div class="flex flex-col gap-8 pt-4">
        <div v-for="group in groupedAgents" :key="group.agentClass">
          <div v-if="!searchQuery && !status && !agentClass" class="pb-4">
            <div class="flex items-center gap-2 pb-2">
              <Icon :name="group.icon" size="2em" class="text-surface-500" />
              <span class="text-lg font-medium">{{ group.name }}</span>
              <Button v-if="group.networkGraph" v-tooltip.top="t('agent.workflow.view_tooltip')" severity="secondary"
                text rounded size="small" @click="openWorkflowModal(group)">
                <Icon name="mage:arrows-all-direction-2" size="1.25em" />
              </Button>
            </div>
            <span v-if="group.description" class="pb-2 text-xs text-surface-500">
              {{ group.description }}
            </span>
          </div>
          <div class="grid grid-cols-3 gap-4">
            <AgentCard v-for="agent in group.instances" :key="`${agent.agent_class}-${agent.agent_id}`" :agent="agent"
              @click="() => toAgent(agent)" @clone="handleClone" />
            <AgentEmptyCard v-if="group.isAvailable && (!searchQuery && !status && !agentClass)"
              @add="openCreateModal(group.agentClass)" />
          </div>
        </div>
        <div v-if="showNoResults" class="flex items-center justify-center text-surface-500">
          <span class="text-xl">{{ t('agent.list.no_results') }}</span>
        </div>
      </div>
      <AgentCreateModal v-model="createModalOpen" :initial-class="selectedClassForCreate"
        :initial-data="initialDataForCreate" @success="handleCreateSuccess" />
      <WorkflowModal v-model="workflowModalOpen" :graph-data="selectedGroupForWorkflow?.networkGraph"
        :header="selectedGroupForWorkflow ? `${t('agent.workflow.title')} — ${selectedGroupForWorkflow.name}` : undefined" />
    </StructuralColumn>

    <NuxtPage />
  </StructuralScreen>
</template>

<script setup lang="ts">
import type { FullAgentInstanceDto, WorkflowGraph } from '@core/sdk/client'

type AgentGroup = {
  agentClass: string
  name: string
  description: string
  icon: string
  instances: FullAgentInstanceDto[]
  isAvailable: boolean
  networkGraph: WorkflowGraph | null
}

const router = useRouter()
const route = useRoute()
const tenantPath = useTenantPath()
const { t, locale } = useI18n()

const { agentInstances, agentInstancesAreLoading, searchQuery, agentClass, status } = useAgentInstances()
const { agentClasses, agentClassesAreLoading } = useAgentClasses()
const { navItems, activeNavItem, toNavItem } = useAgentNavigation()

const isLoading = computed(() => agentInstancesAreLoading.value || agentClassesAreLoading.value)
const isTemplatesRoute = computed(() => route.path.includes('/service/agents/templates'))

const createModalOpen = ref(false)
const selectedClassForCreate = ref('')
const initialDataForCreate = ref<Record<string, unknown> | null>(null)

const workflowModalOpen = ref(false)
const selectedGroupForWorkflow = ref<AgentGroup | null>(null)

const agentClassOptions = computed(() => {
  if (!agentClasses.value) return []

  return agentClasses.value.map(c => ({
    label: c.name?.[locale.value] ?? c.agent_class,
    value: c.agent_class,
  }))
},
)

const statusOptions = computed(() => [
  { label: t('agent.list.filter.enabled'), value: 'enabled' },
  { label: t('agent.list.filter.disabled'), value: 'disabled' },
])

const hasVisibleInstances = computed(() =>
  groupedAgents.value.some(group => group.instances.length > 0),
)

const showNoResults = computed(() =>
  !hasVisibleInstances.value && (!!searchQuery.value || !!agentClass.value || !!status.value),
)

const openWorkflowModal = (group: AgentGroup) => {
  selectedGroupForWorkflow.value = group
  workflowModalOpen.value = true
}

const openCreateModal = (agentClass: string) => {
  selectedClassForCreate.value = agentClass
  initialDataForCreate.value = null
  createModalOpen.value = true
}

const handleClone = (agent: FullAgentInstanceDto) => {
  selectedClassForCreate.value = agent.agent_class
  initialDataForCreate.value = agent.configuration ?? null
  createModalOpen.value = true
}

const groupedAgents = computed<AgentGroup[]>(() => {
  const groups = new Map<string, AgentGroup>()

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
        networkGraph: classInfo.network_graph ?? null,
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
          networkGraph: agent.network_graph ?? null,
        })
      }
    }
  }

  return Array.from(groups.values())
    .sort((a, b) => a.agentClass.localeCompare(b.agentClass))
})

const toAgent = (agent: FullAgentInstanceDto) => {
  router.push(tenantPath(`/service/agents/${agent.agent_class}-${agent.agent_id}/overview`))
}

const handleCreateSuccess = (agentClass: string, agentId: string) => {
  router.push(tenantPath(`/service/agents/${agentClass}-${agentId}/overview`))
}
</script>
