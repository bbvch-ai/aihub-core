<template>
  <VueFlow
    :nodes="nodes"
    :edges="edges"
    :min-zoom="0.2"
    :max-zoom="4"
    fit-view-on-init
    class="size-full"
  >
    <Background />

    <template #node-start="{ id, data }">
      <WorkflowStartNode
        :id="id"
        :data="data"
      />
    </template>

    <template #node-step="{ id, data }">
      <WorkflowStepNode
        :id="id"
        :data="data"
      />
    </template>

    <template #node-stop="{ id, data }">
      <WorkflowStopNode
        :id="id"
        :data="data"
      />
    </template>
  </VueFlow>
</template>

<script setup lang="ts">
import dagre from '@dagrejs/dagre'
import { Background } from '@vue-flow/background'
import { VueFlow, MarkerType, Position, useVueFlow } from '@vue-flow/core'
import { computed, onMounted } from 'vue'

import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'

import type { WorkflowGraph } from '@core/sdk/client'

const NODE_WIDTH = 298
const NODE_HEIGHT = 100

const props = defineProps<{
  graphData: WorkflowGraph
}>()

const { updateNodeInternals, fitView } = useVueFlow()

// Re-measure handle positions after the modal's open animation has settled.
// Without this, vue-flow's initial handleBounds are taken mid-animation and end
// up ~10px off-center, shifting edge endpoints sideways from the actual handles.
onMounted(() => {
  setTimeout(() => {
    updateNodeInternals(props.graphData.nodes.map(n => n.id))
    fitView({ padding: 0.15 })
  }, 350)
})

const layout = computed(() => {
  const g = new dagre.graphlib.Graph()
  g.setDefaultEdgeLabel(() => ({}))
  g.setGraph({ rankdir: 'TB', ranksep: 80, nodesep: 30 })
  props.graphData.nodes.forEach(n => g.setNode(n.id, { width: NODE_WIDTH, height: NODE_HEIGHT }))
  props.graphData.links.forEach(l => g.setEdge(l.source, l.target))
  dagre.layout(g)
  return g
})

const nodes = computed(() => props.graphData.nodes.map((node) => {
  const pos = layout.value.node(node.id)
  return {
    id: node.id,
    type: node.type,
    position: { x: pos.x - NODE_WIDTH / 2, y: pos.y - NODE_HEIGHT / 2 },
    data: node,
    sourcePosition: Position.Bottom,
    targetPosition: Position.Top,
  }
}))

const edges = computed(() => props.graphData.links.map(link => ({
  id: `${link.source}->${link.target}`,
  source: link.source,
  target: link.target,
  animated: true,
  markerEnd: { type: MarkerType.ArrowClosed, width: 24, height: 24 },
})))
</script>

