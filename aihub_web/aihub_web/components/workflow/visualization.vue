<template>
  <div class="vue-flow-wrapper w-full h-[600px]">
    <VueFlow
      :nodes="nodes"
      :edges="edges"
      :default-viewport="{ zoom: 1, x: 0, y: 0 }"
      :node-dimensions-change="true"
      fit-view-on-init
    >
      <template #node-custom="nodeProps">
        <div
          class="custom-node rounded-md shadow-md border p-3 bg-stone-50 dark:bg-stone-950  border-gray-300 dark:border-stone-800"
        >
          <div class="font-semibold text-center text-gray-800 dark:text-gray-50">
            {{ nodeProps.data.label || nodeProps.id }}
          </div>
          <div
            v-if="nodeProps.data.description"
            class="text-sm text-gray-600 mt-1"
          >
            {{ nodeProps.data.description }}
          </div>
        </div>
      </template>
      <Background
        pattern-color="#aaa"
        gap="8"
      />
    </VueFlow>
  </div>
</template>

<script setup>
import { VueFlow, useVueFlow } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import dagre from '@dagrejs/dagre'
import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'

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

const nodes = ref([])
const edges = ref([])
const { fitView } = useVueFlow()

// Transform NetworkX graph data to Vue Flow format
const transformGraph = (networkxGraph) => {
  // Create nodes
  const transformedNodes = networkxGraph.nodes.map((node) => {
    return {
      id: node.id,
      type: 'custom',
      data: {
        label: node.label || node.id,
        description: node.description || '',
      },
      // Position will be set by layout algorithm
      position: { x: 0, y: 0 },
    }
  })

  // Create edges
  const transformedEdges = networkxGraph.links.map((link, index) => ({
    id: `e${index}`,
    source: link.source,
    target: link.target,
    animated: true,
    markerEnd: {
      type: 'arrowclosed',
    },
  }))

  return { nodes: transformedNodes, edges: transformedEdges }
}

onMounted(() => {
  const graphElements = transformGraph(props.graphData)

  // Use dagre to automatically layout the graph
  const dagreGraph = new dagre.graphlib.Graph()
  dagreGraph.setDefaultEdgeLabel(() => ({}))
  dagreGraph.setGraph({ rankdir: 'TB', ranksep: 80 }) // Top to bottom layout

  // Add nodes to dagre
  graphElements.nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: 180, height: node.data.description ? 80 : 40 })
  })

  // Add edges to dagre
  graphElements.edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target)
  })

  // Calculate layout
  dagre.layout(dagreGraph)

  // Apply layout to nodes
  graphElements.nodes.forEach((node) => {
    const nodeWithPosition = dagreGraph.node(node.id)
    node.position = {
      x: nodeWithPosition.x - nodeWithPosition.width / 2,
      y: nodeWithPosition.y - nodeWithPosition.height / 2,
    }
  })

  // Set nodes and edges with positions
  nodes.value = graphElements.nodes
  edges.value = graphElements.edges

  // Fit the view to show all elements
  setTimeout(() => {
    fitView()
  }, 100)
})
</script>

<style scoped>
.custom-node {
  min-width: 150px;
}
</style>
