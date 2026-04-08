<template>
  <StructuralColumn
    :title="t('agent.title')"
    :loading="agentClassesAreLoading"
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
            @click="openCreateModalWithTemplate(group.agentClass, tmpl)"
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
    <AgentCreateModal
      v-model="createModalOpen"
      :initial-class="selectedClassForCreate"
      :initial-data="initialDataForCreate"
      @success="handleCreateSuccess"
    />
  </StructuralColumn>
</template>

<script setup lang="ts">
const router = useRouter()
const tenantPath = useTenantPath()
const { t, locale } = useI18n()

const { agentClasses, agentClassesAreLoading } = useAgentClasses()
const { navItems, activeNavItem, toNavItem } = useAgentNavigation()

const createModalOpen = ref(false)
const selectedClassForCreate = ref('')
const initialDataForCreate = ref<Record<string, unknown> | null>(null)

const openCreateModalWithTemplate = (agentClass: string, template: Record<string, unknown>) => {
  selectedClassForCreate.value = agentClass
  initialDataForCreate.value = template
  createModalOpen.value = true
}

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

const handleCreateSuccess = (agentClass: string, agentId: string) => {
  router.push(tenantPath(`/service/agents/${agentClass}-${agentId}/overview`))
}
</script>
