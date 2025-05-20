<template>
  <StructuralColumn
    title="Nodes"
    close-route="/admin/knowledge"
    :loading="nodesummaryNodesAreLoading"
  >
    <div class="flex flex-col gap-16">
      <div
        v-for="summary in summaryNodes"
        :key="summary.level"
      >
        <template v-if="summary.nodes.length > 0">
          <div class="pl-2 font-bold">
            Level {{ summary.level }}
          </div>
          <KnowledgeNodeContent
            v-for="node in summary.nodes"
            :key="node.id"
            :node="node"
          />
        </template>
      </div>
    </div>
  </StructuralColumn>
</template>

<script setup lang="ts">
import { useSummaryNodes } from '@core/composables/document/useSummaryNodes'

const { summaryNodes, nodesummaryNodesAreLoading } = useSummaryNodes()
</script>

<style scoped>

</style>
