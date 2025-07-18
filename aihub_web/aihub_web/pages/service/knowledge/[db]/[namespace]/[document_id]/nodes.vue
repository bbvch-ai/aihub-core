<template>
  <StructuralColumn
    :title="t('knowledge.nodes.title')"
    :close-route="`/service/knowledge/${route.params.db}/${route.params.namespace}`"
    :loading="nodesAreLoading"
  >
    <KnowledgeNodeContent
      v-for="node in nodes"
      :key="node.id"
      :node="node"
    />
  </StructuralColumn>
</template>

<script setup lang="ts">
const { nodes, nodesAreLoading } = useNodes()

const { t } = useI18n()
const route = useRoute()
</script>
