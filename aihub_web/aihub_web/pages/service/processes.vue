<template>
  <StructuralScreen>
    <StructuralColumn
      :title="t('process.title')"
      :loading="isLoading"
    >
      <div class="flex flex-col gap-12">
        <div
          v-for="group in groupedProcesses"
          :key="group.processClass"
        >
          <div class="flex items-center gap-2 pb-2 pl-2">
            <Icon
              :name="group.icon"
              size="1.25em"
              class="text-surface-500"
            />
            <span class="text-sm font-medium">{{ group.name }}</span>
            <span
              v-if="group.description"
              class="text-xs text-surface-500"
            >
              — {{ group.description }}
            </span>
          </div>
          <div class="grid grid-cols-2 gap-4 2xl:grid-cols-2">
            <ProcessCard
              v-for="process in group.instances"
              :key="`${process.process_class}-${process.process_id}`"
              :process="process"
              @click="() => toProcess(process)"
            />
            <ProcessEmptyCard
              v-if="group.isAvailable"
              @add="openCreateModal(group.processClass)"
            />
          </div>
        </div>
      </div>
      <ProcessCreateModal
        v-model="createModalOpen"
        :initial-class="selectedClassForCreate"
        @success="handleCreateSuccess"
      />
    </StructuralColumn>

    <NuxtPage />
  </StructuralScreen>
</template>

<script setup lang="ts">
import type { FullProcessInstanceDtoReadable } from '@core/sdk/client'

import { useLocalePath } from '#i18n'

const router = useRouter()
const localePath = useLocalePath()
const { t, locale } = useI18n()

const { processInstances, processInstancesAreLoading } = useProcessInstances()
const { processClasses, processClassesAreLoading } = useProcessClasses()

const isLoading = computed(() => processInstancesAreLoading.value || processClassesAreLoading.value)

const createModalOpen = ref(false)
const selectedClassForCreate = ref('')

const openCreateModal = (processClass: string) => {
  selectedClassForCreate.value = processClass
  createModalOpen.value = true
}

const groupedProcesses = computed(() => {
  const groups = new Map<string, {
    processClass: string
    name: string
    description: string
    icon: string
    instances: FullProcessInstanceDtoReadable[]
    isAvailable: boolean
  }>()

  const localeKey = locale.value as 'de' | 'en' | 'fr' | 'it'

  // First, add all available process classes (even those without instances)
  if (processClasses.value) {
    for (const classInfo of processClasses.value) {
      groups.set(classInfo.process_class, {
        processClass: classInfo.process_class,
        name: classInfo.name?.[localeKey] ?? classInfo.process_class,
        description: classInfo.description?.[localeKey] ?? '',
        icon: classInfo.icon ?? 'carbon:ibm-event-processing',
        instances: [],
        isAvailable: true,
      })
    }
  }

  // Then, add instances to their groups (or create groups for unavailable classes)
  if (processInstances.value) {
    for (const process of processInstances.value) {
      const existing = groups.get(process.process_class)
      if (existing) {
        existing.instances.push(process)
      }
      else {
        // Class not available - create group but mark as unavailable
        groups.set(process.process_class, {
          processClass: process.process_class,
          name: process.process_class,
          description: '',
          icon: 'carbon:ibm-event-processing',
          instances: [process],
          isAvailable: false,
        })
      }
    }
  }

  return Array.from(groups.values())
    .sort((a, b) => a.processClass.localeCompare(b.processClass))
})

const toProcess = (process: FullProcessInstanceDtoReadable) => {
  router.push(localePath(`/service/processes/${process.process_class}-${process.process_id}/overview`))
}

const handleCreateSuccess = (processClass: string, processId: string) => {
  router.push(localePath(`/service/processes/${processClass}-${processId}/overview`))
}
</script>
