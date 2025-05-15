<template>
  <StructuralScreen>
    <StructuralColumn
      title="Test"
      :loading="namespacesAreLoading"
    >
      <div
        v-for="namespace in namespaces"
        :key="namespace.name"
        @click="() => toNamespace(namespace)"
      >
        {{ namespace.name }}
      </div>
    </StructuralColumn>
    <NuxtPage />
  </StructuralScreen>
</template>

<script setup lang="ts">
import type { Namespace } from '@core/sdk/client'

import { useLocalePath } from '#i18n'

const router = useRouter()
const localePath = useLocalePath()

const { namespaces, namespacesAreLoading } = useNamespaces()

const toNamespace = (namespace: Namespace) => {
  router.push(localePath(`/admin/knowledge/${namespace.name}`))
}
</script>
