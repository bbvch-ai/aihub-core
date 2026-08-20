<template>
  <div class="flex flex-col gap-4">
    <!-- Agent Class Selection -->
    <div>
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
    classPlaceholder?: string
    idPlaceholder?: string
    filter?: boolean
  }
}

const props = defineProps<AgentSelectorProps>()
const { t, locale } = useI18n()

// Get custom props from context (FormKit passes them there, not as direct props)
const startEvent = computed(() => props.context.startEvent)
const classPlaceholder = computed(() => props.context.classPlaceholder)
const idPlaceholder = computed(() => props.context.idPlaceholder)
const filter = computed(() => props.context.filter ?? true)

// Get current value from context
const currentValue = computed(() => props.context.value ?? null)

// Shared cached queries rather than per-mount fetches: a form renders several of these and
// re-renders remount them, which previously issued one request per mount. Instances follow the
// selected class through the query key, so no imperative refetch on selection.
const { agentClasses: fetchedClasses, agentClassesAreLoading: isLoading } = useAgentClasses()
const agentClasses = computed<AgentClassDto[]>(() => fetchedClasses.value ?? [])

const { agentInstances: fetchedInstances, agentInstancesAreLoading: isLoadingInstances }
  = useAgentInstancesByClass(() => currentValue.value?.agent_class)
const agentInstances = computed<FullAgentInstanceDto[]>(() => fetchedInstances.value ?? [])

// Selected class (computed property that syncs with the form value)
const selectedClass = computed({
  get: () => currentValue.value?.agent_class ?? null,
  set: (value: string | null) => {
    if (value) {
      // Resetting the id re-keys the instances query onto the new class.
      emitValue(value, '')
    }
    else {
      props.context.node.input(null)
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

// Clear the selection if a changed startEvent filter no longer admits the selected class.
watch(startEvent, () => {
  if (selectedClass.value && !filteredClassOptions.value.some(opt => opt.name === selectedClass.value)) {
    props.context.node.input(null)
  }
})
</script>
