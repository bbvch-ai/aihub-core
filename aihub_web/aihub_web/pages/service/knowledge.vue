<template>
  <StructuralScreen>
    <StructuralColumn
      :title="t('knowledge.title')"
      :loading="databasesAreLoading"
    >
      <div class="flex flex-col gap-12">
        <div
          v-for="database in databases"
          :key="database.name"
        >
          <div
            class="pb-2 pl-2 text-sm font-medium"
          >
            {{ useChangeCase(database.name, 'capitalCase') }}
          </div>
          <div
            class="grid grid-cols-2 gap-4 2xl:grid-cols-2"
          >
            <KnowledgeNamespaceCard
              v-for="namespace in database.namespaces"
              :key="namespace.name"
              :namespace="namespace"
              @click="() => toNamespace(namespace)"
            />
          </div>
        </div>
      </div>
    </StructuralColumn>
    <NuxtPage />
  </StructuralScreen>
</template>

<script setup lang="ts">
import { useChangeCase } from '@vueuse/integrations/useChangeCase'

import type { Namespace } from '@core/sdk/client'

import { useLocalePath } from '#i18n'

const router = useRouter()
const localePath = useLocalePath()
const { t } = useI18n()

const { databases, databasesAreLoading } = useDatabases()

const toNamespace = (namespace: Namespace) => {
  router.push(localePath(`/service/knowledge/${namespace.database}/${namespace.name}`))
}
</script>
