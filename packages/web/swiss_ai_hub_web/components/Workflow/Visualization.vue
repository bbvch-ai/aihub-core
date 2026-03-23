<template>
  <VueFlow
    v-model:nodes="nodes"
    v-model:edges="edges"
    :default-viewport="{ zoom: 1 }"
    :min-zoom="0.2"
    :max-zoom="4"
    class="size-full"
    fit-view-on-init
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

    <template #edge-custom="customEdgeProps">
      <WorkflowEventEdge
        :id="customEdgeProps.id"
        :source-x="customEdgeProps.sourceX"
        :source-y="customEdgeProps.sourceY"
        :target-x="customEdgeProps.targetX"
        :target-y="customEdgeProps.targetY"
        :source-position="customEdgeProps.sourcePosition"
        :target-position="customEdgeProps.targetPosition"
        :data="customEdgeProps.data satisfies EdgeData"
        :marker-end="customEdgeProps.markerEnd"
        :style="customEdgeProps.style"
      />
    </template>
  </VueFlow>
</template>

<script setup lang="ts">
import dagre from '@dagrejs/dagre'
import { Background } from '@vue-flow/background'
import { VueFlow, useVueFlow, MarkerType } from '@vue-flow/core'
import { ref, watchEffect } from 'vue'

// Import styles
import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'

import type { WorkflowGraph, NodeData, EdgeData } from '@core/sdk/client'
import type { Node, Edge } from '@vue-flow/core'

const props = defineProps<{
  graphData: WorkflowGraph
}>()

const { fitView } = useVueFlow()
const nodes = ref<Node<NodeData>[]>([])
const edges = ref<Edge<EdgeData>[]>([])

// Transform the networkx graph to vue-flow format
const transformGraphData = () => {
  // Create Vue Flow nodes
  const graphNodes = props.graphData.nodes.map((node) => {
    const nodeId = node.id || node.node_id || node.label
    return {
      id: nodeId,
      type: node.type,
      position: { x: 0, y: 0 }, // Initial position, will be calculated by dagre
      data: {
        ...node,
        label: node.label,
      },
    }
  })

  // Create Vue Flow edges
  const graphEdges = props.graphData.links.map((link, index) => {
    const edgeId = `e-${index}`

    return {
      id: edgeId,
      source: link.source,
      target: link.target,
      animated: true,
      label: link.event_name || '',
      data: link,
      markerEnd: MarkerType.Arrow,
      type: 'custom',
    }
  })

  // Apply dagre layout
  const dagreGraph = new dagre.graphlib.Graph()
  dagreGraph.setDefaultEdgeLabel(() => ({}))
  dagreGraph.setGraph({ rankdir: 'LR' }) // Left to Right layout

  // Add nodes to dagre
  graphNodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: 700, height: 350 })
  })

  // Add edges to dagre
  graphEdges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target)
  })

  // Calculate the layout
  dagre.layout(dagreGraph)

  // Apply the calculated layout
  const nodesWithPositions = graphNodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id)
    if (nodeWithPosition) {
      node.position = {
        x: nodeWithPosition.x - 100, // Adjust to center the node
        y: nodeWithPosition.y - 30, // Adjust to center the node
      }
    }
    return node
  })

  nodes.value = nodesWithPositions
  edges.value = graphEdges

  // Allow the DOM to update before fitting view
  setTimeout(() => {
    fitView({ padding: 0.2 })
  }, 100)
}

// Watch for changes in the graph data and update the visualization
watchEffect(() => {
  if (
    props.graphData
    && props.graphData.nodes
    && props.graphData.nodes.length
    && props.graphData.links
    && props.graphData.links.length
  ) {
    transformGraphData()
  }
})
</script>
