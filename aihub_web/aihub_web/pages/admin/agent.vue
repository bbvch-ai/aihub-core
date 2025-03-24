<template>
  <div
    class="gap-18 mt-12 flex flex-col p-1"
  >
    <div class="flex flex-col gap-2 p-6">
      <p class="text-3xl font-bold">
        Agents
      </p>
      <p class="text-sm">
        Hier werden alle Agenten dargestellt, mit welchen kommuniziert werden kann
      </p>
    </div>
    <Splitter
      class="mb-8 !border-none "
      :gutter-size="3"
    >
      <SplitterPanel
        state-key="agents"
        state-storage="local"
        :min-size="25"
        :size="25"
        class="border-none bg-stone-50 p-5 dark:bg-stone-950"
      >
        <div
          ref="leftsplitter"
          class="overflow-auto rounded-lg border border-stone-200 dark:border-stone-700"
        >
          <DataTable
            v-if="showTable"
            v-model:filters="filters"
            v-model:selection="selectedAgent"
            striped-rows
            paginator
            removable-sort
            data-key="agent_id"
            sort-mode="multiple"
            :rows="10"
            :rows-per-page-options="[5, 10, 20, 50]"
            :value="agents"
            :loading="agentsLoadingState === 'pending'"
            :global-filter-fields="['agent_id', 'agent_class']"
            selection-mode="single"
          >
            <template #header>
              <div class="flex justify-between">
                <IconField>
                  <InputIcon>
                    <i class="pi pi-search" />
                  </InputIcon>
                  <InputText
                    v-model="filters['global'].value"
                    placeholder="Keyword Search"
                  />
                </IconField>
              </div>
            </template>
            <template #empty>
              No Agents found.
            </template>
            <template #loading>
              Discovering Agents. Please wait.
            </template>
            <Column
              selection-mode="single"
              header-style="width: 3rem"
            />

            <Column
              header="Agent"
              filter-field="agent_config.icon"
            >
              <template #body="{ data: agent }">
                <div class="flex flex-row gap-2 font-bold">
                  <Icon
                    :name="agent.agent_config.icon"
                    size="xl"
                  />
                  <span>{{ agent.agent_config.name }}</span>
                </div>
              </template>
            </Column>
            <Column
              header="Typ"
            >
              <template #body="{ data: agent }">
                <Tag
                  :value="agent.agent_class"
                  severity="info"
                />
              </template>
            </Column>
            <Column
              header="Conversable"
            >
              <template #body="{ data: agent }">
                <i
                  :class="agent.is_conversational ? 'pi pi-check-circle' : 'pi pi-times-circle'"
                  style="font-size: 1rem"
                />
              </template>
            </Column>
            <template #paginatorstart>
              <Button
                type="button"
                icon="pi pi-refresh"
                text
                @click="agentStore.refetchAgents"
              />
            </template>
            <template #paginatorend>
              <Button
                type="button"
                icon="pi pi-download"
                text
              />
            </template>
          </DataTable>
          <DataView
            v-else
            :value="agents"
            class="bg-white p-3 dark:bg-stone-900"
            paginator
            :rows="5"
          >
            <template #header>
              <IconField>
                <InputIcon>
                  <i class="pi pi-search" />
                </InputIcon>
                <InputText
                  v-model="filters['global'].value"
                  placeholder="Keyword Search"
                />
              </IconField>
            </template>
            <template #list="{ items: agentList }">
              <div
                v-for="(agent, index) in agentList"
                :key="agent.agent_id"
              >
                <div
                  class="flex flex-row gap-4 p-4"
                  :class="{
                    'border-t border-surface-200 dark:border-surface-700': index !== 0,
                    'bg-stone-50 dark:bg-stone-950': selectedAgent?.agent_id == agent.agent_id,
                  }"
                >
                  <Checkbox
                    binary
                    :model-value="selectedAgent?.agent_id == agent.agent_id"
                    variant="filled"
                    @update:model-value="selectedAgent = selectedAgent?.agent_id == agent.agent_id ? null : agent"
                  />
                  <div
                    class="flex flex-col items-start gap-4"
                  >
                    <div class="flex flex-row gap-2 font-bold">
                      <Icon
                        :name="agent.agent_config.icon"
                        size="xl"
                      />
                      <span>{{ agent.agent_config.name }}</span>
                    </div>
                    <Tag
                      :value="agent.agent_class"
                      severity="info"
                    />
                  </div>
                </div>
              </div>
            </template>
          </DataView>
        </div>
      </SplitterPanel>
      <SplitterPanel
        v-if="selectedAgent"
        class="border-none bg-stone-50 p-5 dark:bg-stone-950"
      >
        <NuxtPage />
      </SplitterPanel>
    </Splitter>
  </div>
</template>

<script setup lang="ts">
import { useAgentsStore } from '@core/stores/useAgentsStore'
import { FilterMatchMode } from '@primevue/core/api'

import type { AgentDto } from '@core/sdk/client'

import { useLocalePath } from '#i18n'

const router = useRouter()
const agentStore = useAgentsStore()
const { agents, agentsLoadingState } = storeToRefs(agentStore)

const selectedAgent = ref<AgentDto | null>(null)

const localePath = useLocalePath()
watch(selectedAgent, (agent: AgentDto | null) => {
  if (agent) {
    router.push(localePath(`/admin/agent/agent-${agent.agent_id}-${agent.agent_class}`))
  }
  else {
    router.push(localePath('/admin/agent'))
  }
})

const filters = ref({
  global: { value: null, matchMode: FilterMatchMode.CONTAINS },
  agent_id: { value: null, matchMode: FilterMatchMode.STARTS_WITH },
  agent_name: { value: null, matchMode: FilterMatchMode.STARTS_WITH },
})

const leftSplitter = useTemplateRef('leftsplitter')
const { width: leftSplitterWidth } = useElementSize(leftSplitter)
const showTable = computed(() => leftSplitterWidth.value > 500)
</script>

<style scoped>

</style>
