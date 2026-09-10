<template>
  <div class="flex flex-col gap-4">
    <!-- Agent Class Selection (omitted when the config pins the class) -->
    <div v-if="!pinnedClass">
      <label
        for="agent-class-select"
        class="mb-1 block text-sm font-medium"
      >
        {{ t('agent.selector.class.label') }}
      </label>
      <Select
        v-model="selectedClass"
        :aria-label="t('agent.selector.class.label')"
        input-id="agent-class-select"
        :options="filteredClassOptions"
        option-label="displayName"
        option-value="name"
        :placeholder="classPlaceholder ?? t('agent.selector.class.placeholder')"
        :filter="filter"
        :loading="isLoading"
        class="w-full"
      >
        <template #option="{ option }">
          <div class="flex items-center gap-2">
            <Icon
              :name="option.icon || 'mage:robot'"
              size="1.2em"
            />
            <span>{{ option.displayName }}</span>
          </div>
        </template>
        <template #value="{ value }">
          <div
            v-if="value"
            class="flex items-center gap-2"
          >
            <Icon
              :name="getClassIcon(value)"
              size="1.2em"
            />
            <span>{{ getClassDisplayName(value) }}</span>
          </div>
        </template>
      </Select>
    </div>

    <!-- Agent ID Selection (shown when class selected) -->
    <div v-if="selectedClass">
      <label
        for="agent-id-select"
        class="mb-1 block text-sm font-medium"
      >
        {{ t('agent.selector.id.label') }}
      </label>
      <Select
        v-model="selectedId"
        :aria-label="t('agent.selector.id.label')"
        input-id="agent-id-select"
        :options="idOptions"
        option-label="displayName"
        option-value="id"
        :placeholder="idPlaceholder ?? t('agent.selector.id.placeholder')"
        :filter="filter"
        :loading="isLoadingInstances"
        class="w-full"
      >
        <template #option="{ option }">
          <div class="flex items-center gap-2">
            <Icon
              :name="option.icon || 'mage:user'"
              size="1.2em"
            />
            <span>{{ option.displayName }}</span>
          </div>
        </template>
        <template #value="{ value }">
          <div
            v-if="value"
            class="flex items-center gap-2"
          >
            <Icon
              :name="getIdIcon(value)"
              size="1.2em"
            />
            <span>{{ getIdDisplayName(value) }}</span>
          </div>
        </template>
      </Select>
      <small class="mt-1 text-surface-500">
        {{ t('agent.selector.id.help') }}
      </small>
    </div>
  </div>
</template>

<script setup lang="ts">
import { getAgentClasses, getAgentClassInstances } from '@core/sdk/client'
import { capitalCase } from 'change-case'

import type { AgentClassDto, FullAgentInstanceDto, LocaleString } from '@core/sdk/client'

/**
 * Extracts the localized string from a LocaleString object.
 * Falls back to first available value if the requested locale is not available.
 */
function getLocalizedValue(localeString: LocaleString | string | undefined, locale: string): string {
  if (!localeString) return ''
  if (typeof localeString === 'string') return localeString

  // LocaleString object - try to get the current locale, fallback to en, then any
  return (localeString as Record<string, string>)[locale]
    || (localeString as Record<string, string>).en
    || Object.values(localeString)[0]
    || ''
}

interface AgentSelectorValue {
  agent_class: string
  agent_id: string
}

interface ClassOption {
  name: string
  displayName: string
  icon: string
}

interface IdOption {
  id: string
  displayName: string
  icon: string
}

interface AgentSelectorProps {
  context: {
    node: {
      input: (value: AgentSelectorValue | null) => void
    }
    value?: AgentSelectorValue | null
    attrs: Record<string, unknown>
    startEvent?: string
    agentClass?: string
    classPlaceholder?: string
    idPlaceholder?: string
    filter?: boolean
  }
}

const props = defineProps<AgentSelectorProps>()
const { t, locale } = useI18n()
const { tenantId } = useTenant()

// Get custom props from context (FormKit passes them there, not as direct props)
const startEvent = computed(() => props.context.startEvent)
// Set by configs that already know which blueprint answers: the class dropdown is not rendered and only
// this class's profiles are offered.
const pinnedClass = computed(() => props.context.agentClass)
const classPlaceholder = computed(() => props.context.classPlaceholder)
const idPlaceholder = computed(() => props.context.idPlaceholder)
const filter = computed(() => props.context.filter ?? true)

// State
const agentClasses = ref<AgentClassDto[]>([])
const agentInstances = ref<FullAgentInstanceDto[]>([])
const isLoading = ref(false)
const isLoadingInstances = ref(false)

// Get current value from context
const currentValue = computed(() => props.context.value ?? null)

// Selected class (computed property that syncs with the form value)
const selectedClass = computed({
  get: () => currentValue.value?.agent_class ?? pinnedClass.value ?? null,
  set: (value: string | null) => {
    if (value) {
      // When class changes, reset agent ID and fetch instances
      emitValue(value, '')
      fetchInstances(value)
    }
    else {
      props.context.node.input(null)
      agentInstances.value = []
    }
  },
})

// Selected agent ID (computed property that syncs with the form value)
const selectedId = computed({
  get: () => currentValue.value?.agent_id ?? null,
  set: (value: string | null) => {
    if (selectedClass.value && value) {
      emitValue(selectedClass.value, value)
    }
  },
})

// Emit complete value object
function emitValue(agentClass: string, agentId: string) {
  props.context.node.input({
    agent_class: agentClass,
    agent_id: agentId,
  })
}

// Class options for select
const classOptions = computed<ClassOption[]>(() =>
  agentClasses.value.map(cls => ({
    name: cls.agent_class,
    displayName: getLocalizedValue(cls.name, locale.value) || capitalCase(cls.agent_class),
    icon: cls.icon || 'mage:robot',
  })),
)

// Filtered class options based on startEvent
const filteredClassOptions = computed<ClassOption[]>(() => {
  if (!startEvent.value) return classOptions.value // No filter = show all

  return classOptions.value.filter((classOption) => {
    const agentClass = agentClasses.value.find(c => c.agent_class === classOption.name)
    if (!agentClass) return false

    // Check if any start_event matches the filter
    return agentClass.start_events.some(event =>
      event.event_name === startEvent.value
      || event.event_parents.includes(startEvent.value!),
    )
  })
})

// ID options based on selected class
const idOptions = computed<IdOption[]>(() => {
  return agentInstances.value.map(instance => ({
    id: instance.agent_config.agent_id,
    displayName: instance.agent_config.name || instance.agent_config.agent_id,
    icon: instance.agent_config.icon || 'mage:user',
  }))
})

function getClassIcon(name: string): string {
  const option = classOptions.value.find(opt => opt.name === name)
  return option?.icon ?? 'mage:robot'
}

function getClassDisplayName(name: string): string {
  const option = classOptions.value.find(opt => opt.name === name)
  return option?.displayName ?? name
}

function getIdIcon(id: string): string {
  const option = idOptions.value.find(opt => opt.id === id)
  return option?.icon ?? 'mage:user'
}

function getIdDisplayName(id: string): string {
  const option = idOptions.value.find(opt => opt.id === id)
  return option?.displayName ?? id
}

async function fetchClasses() {
  isLoading.value = true
  try {
    const response = await getAgentClasses({
      composable: '$fetch',
      path: { tenant_id: tenantId.value! },
    })
    agentClasses.value = response
  }
  catch (error) {
    console.error('Failed to fetch agent classes:', error)
    agentClasses.value = []
  }
  finally {
    isLoading.value = false
  }
}

async function fetchInstances(agentClass: string) {
  isLoadingInstances.value = true
  try {
    const response = await getAgentClassInstances({
      composable: '$fetch',
      path: { tenant_id: tenantId.value!, agent_class: agentClass },
    })
    agentInstances.value = response
  }
  catch (error) {
    console.error(`Failed to fetch instances for class "${agentClass}":`, error)
    agentInstances.value = []
  }
  finally {
    isLoadingInstances.value = false
  }
}

// Fetch classes on mount
onMounted(() => {
  // A pinned class needs no class list — nothing renders it, and the profile dropdown is driven by
  // fetchInstances alone.
  if (!pinnedClass.value) {
    fetchClasses()
  }

  // Pinned, or already chosen: either way the profile dropdown needs that class's instances up front.
  const classToLoad = currentValue.value?.agent_class ?? pinnedClass.value
  if (classToLoad) {
    fetchInstances(classToLoad)
  }
})

// Refetch if startEvent changes
watch(startEvent, () => {
  // A pinned class is not filtered by start event, and its class list is never fetched — so the check below
  // would find no match and clear a perfectly valid selection.
  if (pinnedClass.value) return

  // Clear selection if current class no longer matches filter
  if (selectedClass.value && !filteredClassOptions.value.some(opt => opt.name === selectedClass.value)) {
    props.context.node.input(null)
    agentInstances.value = []
  }
})
</script>
