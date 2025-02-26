<template>
  <div
    class="p-6"
  >
    <Splitter
      style="height: 300px"
      class="mb-8"
    >
      <SplitterPanel
        state-key="agents"
        state-storage="local"
      >
        <div class="card">
          <DataTable
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
                <div>
                  <p class="text-xl font-bold">
                    Agents
                  </p>
                  <p class="text-sm">
                    Hier werden alle Agenten dargestellt, mit welchen kommuniziert werden kann
                  </p>
                </div>
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
              <template #body="{ data }">
                <div class="flex flex-row gap-2">
                  <Icon
                    :name="data.agent_config.icon"
                    size="xl"
                  />
                  <span>{{ data.agent_config.name }}</span>
                </div>
              </template>
            </Column>
            <Column
              sortable
              field="agent_id"
              header="ID"
            />
            <Column
              sortable
              field="agent_class"
              header="Class"
            />
            <Column
              header="type"
              style="min-width: 100px"
            >
              <template #body="{ data }">
                <Tag
                  :value="data.agent_id"
                  severity="info"
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
        </div>
        {{ agent }}
      </SplitterPanel>
      <SplitterPanel>
        <NuxtPage />
      </SplitterPanel>
    </Splitter>
  </div>
</template>

<script setup lang="ts">
import { FilterMatchMode } from '@primevue/core/api'

import { useAgentsStore } from '@core/stores/useAgentsStore'
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
</script>

<style scoped>

</style>
