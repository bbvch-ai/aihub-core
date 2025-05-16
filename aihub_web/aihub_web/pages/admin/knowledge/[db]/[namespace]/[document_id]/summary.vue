<template>
  <StructuralColumn
    title="Nodes"
    close-route="/admin/knowledge"
    :loading="nodesummaryNodesAreLoading"
  >
    <div
      v-for="summary in summaryNodes"
      :key="summary.level"
    >
      {{ summary.level }}
      <KnowledgeNodeContent
        v-for="node in summary.nodes"
        :key="node.id"
        :node="node"
      />
    </div>
  </StructuralColumn>
</template>

<script setup lang="ts">
import { useSummaryNodes } from '@core/composables/document/useSummaryNodes'

const { summaryNodes, nodesummaryNodesAreLoading } = useSummaryNodes()
</script>

<style scoped>

</style>
