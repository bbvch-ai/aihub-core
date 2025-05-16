<template>
  <StructuralColumn
    title="Nodes"
    close-route="/admin/knowledge"
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
</script>

<style scoped>

</style>
