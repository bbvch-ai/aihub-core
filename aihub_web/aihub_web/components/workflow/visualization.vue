<template>
  <div class="vue-flow-wrapper">
    <VueFlow
      v-model:nodes="nodes"
      v-model:edges="edges"
      :default-viewport="{ zoom: 1 }"
      :min-zoom="0.2"
      :max-zoom="4"
      class="graph-flow"
      fit-view-on-init
    >
      <Background />
      <Controls />
      <MiniMap />

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
  </div>
</template>

<script setup>
import { ref, watchEffect } from 'vue'
import { VueFlow, useVueFlow, MarkerType } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import { MiniMap } from '@vue-flow/minimap'
import dagre from '@dagrejs/dagre'

// Import styles
import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'
import '@vue-flow/controls/dist/style.css'
import '@vue-flow/minimap/dist/style.css'

const props = defineProps({
  graphData: {
    type: Object,
    required: true,
    default: () => ({
      directed: true,
      multigraph: false,
      graph: {},
      nodes: [],
      links: [],
    }),
  },
})

const { fitView } = useVueFlow()
const nodes = ref([])
const edges = ref([])

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
      label: link.event_type || '',
      data: link,
      markerEnd: MarkerType.Arrow,
    }
  })

  // Apply dagre layout
  const dagreGraph = new dagre.graphlib.Graph()
  dagreGraph.setDefaultEdgeLabel(() => ({}))
  dagreGraph.setGraph({ rankdir: 'LR' }) // Left to Right layout

  // Add nodes to dagre
  graphNodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: 600, height: 250 })
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

<style scoped>
.vue-flow-wrapper {
  width: 100%;
  height: 600px;
}

.graph-flow {
  width: 100%;
  height: 100%;
}
</style>
