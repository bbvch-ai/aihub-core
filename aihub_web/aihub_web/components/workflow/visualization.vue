<template>
  <div class="vue-flow-wrapper w-full h-[700px]">
    <VueFlow
      v-model="elements"
      :default-viewport="{ zoom: 1, x: 0, y: 0 }"
      :node-dimensions-change="true"
      fit-view-on-init
    >
      <!-- Step Node Template -->
      <template #node-step="nodeProps">
        <div class="step-node rounded-md shadow-md border p-3 bg-sky-50 dark:bg-sky-950 border-sky-300 dark:border-sky-800">
          <div class="font-semibold text-center text-gray-800 dark:text-gray-50">
            {{ nodeProps.data.label || nodeProps.id }}
          </div>
          <div
            v-if="nodeProps.data.description"
            class="text-sm text-gray-600 dark:text-gray-300 mt-1"
          >
            {{ nodeProps.data.description }}
          </div>

          <!-- Add handles for input/output connections -->
          <template
            v-for="i in nodeProps.data.total_inputs || 0"
            :key="`input-${i-1}`"
          >
            <Handle
              :id="`input-${i-1}`"
              type="target"
              :position="Position.Left"
              :style="getHandleStyle('input', i-1, nodeProps.data.total_inputs)"
            />
          </template>

          <template
            v-for="i in nodeProps.data.total_outputs || 0"
            :key="`output-${i-1}`"
          >
            <Handle
              :id="`output-${i-1}`"
              type="source"
              :position="Position.Right"
              :style="getHandleStyle('output', i-1, nodeProps.data.total_outputs)"
            />
          </template>
        </div>
      </template>

      <!-- Special Node Template (Start/End) -->
      <template #node-special="nodeProps">
        <div class="special-node rounded-md shadow-md border p-3 bg-gray-100 dark:bg-gray-800 border-gray-300 dark:border-gray-700">
          <div class="font-semibold text-center text-gray-800 dark:text-gray-50">
            {{ nodeProps.data.label || nodeProps.id }}
          </div>

          <!-- Special nodes have one handle per connected event -->
          <template v-if="nodeProps.id === 'start'">
            <Handle
              v-for="i in nodeProps.data.total_outputs || 0"
              :id="`output-${i-1}`"
              :key="`output-${i-1}`"
              type="source"
              :position="Position.Right"
              :style="getHandleStyle('output', i-1, nodeProps.data.total_outputs)"
            />
          </template>

          <template v-if="nodeProps.id === 'end'">
            <Handle
              v-for="i in nodeProps.data.total_inputs || 0"
              :id="`input-${i-1}`"
              :key="`input-${i-1}`"
              type="target"
              :position="Position.Left"
              :style="getHandleStyle('input', i-1, nodeProps.data.total_inputs)"
            />
          </template>
        </div>
      </template>

      <!-- Custom Edge with Event Label -->
      <template #edge-default="edgeProps">
        <BaseEdge
          :id="edgeProps.id"
          :path="edgeProps.path"
          :marker-end="edgeProps.markerEnd"
          class="vue-flow__edge-path-selector"
        />
        <EdgeLabelRenderer>
          <div
            :style="{
              position: 'absolute',
              transform: `translate(-50%, -50%) translate(${edgeProps.labelX}px, ${edgeProps.labelY}px)`,
              pointerEvents: 'all',
              background: 'white',
              padding: '4px 8px',
              borderRadius: '4px',
              fontSize: '12px',
              fontWeight: '500',
              border: '1px solid #ccc',
              cursor: 'pointer',
            }"
            class="edge-label"
            @click="showEventDetails(edgeProps.data)"
          >
            {{ edgeProps.data?.event_type || '?' }}
          </div>
        </EdgeLabelRenderer>
      </template>

      <Background
        pattern-color="#aaa"
        gap="8"
      />
      <Controls />
      <MiniMap />
    </VueFlow>

    <!-- Event Details Drawer -->
    <div
      v-if="selectedEvent"
      class="event-details-drawer fixed right-0 top-0 h-full w-96 bg-white dark:bg-gray-900 shadow-xl p-4 overflow-y-auto z-50 transform transition-transform"
    >
      <div class="flex justify-between items-center mb-4">
        <h2 class="text-lg font-bold">
          {{ selectedEvent.event_type }}
        </h2>
        <button
          class="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
          @click="selectedEvent = null"
        >
          <span class="text-xl">&times;</span>
        </button>
      </div>

      <div class="event-info">
        <div class="mb-4">
          <div class="text-sm text-gray-500 dark:text-gray-400">
            Full Name
          </div>
          <div class="font-mono text-xs bg-gray-100 dark:bg-gray-800 p-2 rounded">
            {{ selectedEvent.event_full_name }}
          </div>
        </div>

        <div class="mb-4">
          <div class="text-sm text-gray-500 dark:text-gray-400">
            Event Type
          </div>
          <div class="flex gap-2 mt-1">
            <span
              v-if="selectedEvent.is_start_event"
              class="px-2 py-1 bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 text-xs rounded"
            >Start Event</span>
            <span
              v-if="selectedEvent.is_stop_event"
              class="px-2 py-1 bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200 text-xs rounded"
            >Stop Event</span>
            <span
              v-if="!selectedEvent.is_start_event && !selectedEvent.is_stop_event"
              class="px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 text-xs rounded"
            >Control Event</span>
          </div>
        </div>

        <div v-if="Object.keys(selectedEvent.payload || {}).length > 0">
          <div class="text-sm text-gray-500 dark:text-gray-400 mb-2">
            Payload Fields
          </div>
          <div
            v-for="(info, field) in selectedEvent.payload"
            :key="field"
            class="mb-3 pl-2 border-l-2 border-gray-300 dark:border-gray-700"
          >
            <div class="font-medium">
              {{ field }}
            </div>
            <div class="text-xs text-gray-600 dark:text-gray-400">
              Type: <span class="font-mono">{{ info.type }}</span>
            </div>
            <div
              v-if="info.description"
              class="text-xs text-gray-600 dark:text-gray-400 mt-1"
            >
              {{ info.description }}
            </div>
          </div>
        </div>

        <div
          v-else
          class="text-sm text-gray-500 dark:text-gray-400"
        >
          No payload fields defined for this event.
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import {
  VueFlow,
  useVueFlow,
  Position,
  BaseEdge,
  EdgeLabelRenderer,
  Handle,
  getBezierPath,
} from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import { MiniMap } from '@vue-flow/minimap'
import dagre from '@dagrejs/dagre'
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

const elements = ref([])
const selectedEvent = ref(null)
const { fitView } = useVueFlow()

// Show event details when clicking an edge label
const showEventDetails = (eventData) => {
  selectedEvent.value = eventData
}

// Calculate handle positioning based on index and total count
const getHandleStyle = (type, index, totalCount) => {
  if (totalCount <= 1) {
    return {} // Center position (default)
  }

  // Calculate position percentage along the edge
  const percentage = totalCount > 1 ? index / (totalCount - 1) : 0.5

  // Convert to a CSS position value
  const position = `${Math.round(percentage * 100)}%`

  return {
    top: position,
    bottom: 'auto',
  }
}

// Transform NetworkX graph data to Vue Flow format
const transformGraph = (networkxGraph) => {
  // Create nodes
  const transformedNodes = networkxGraph.nodes.map((node) => {
    return {
      id: node.id,
      type: node.type || 'step',
      position: { x: 0, y: 0 }, // Position will be set by layout algorithm
      data: {
        ...node, // Pass all node data
        label: node.label || node.id,
      },
    }
  })

  // Create edges with custom handles based on position indices
  const transformedEdges = networkxGraph.links.map((link, index) => {
    // Determine source and target handle IDs based on position indices
    const sourceHandleId = `output-${link.source_position || 0}`
    const targetHandleId = `input-${link.target_position || 0}`

    return {
      id: `e${index}`,
      source: link.source,
      target: link.target,
      sourceHandle: sourceHandleId,
      targetHandle: targetHandleId,
      type: 'default',
      animated: link.is_start_event || link.is_stop_event,
      data: {
        // Store all event data for display in the drawer
        event_type: link.event_type || '',
        event_full_name: link.event_full_name || '',
        is_start_event: link.is_start_event || false,
        is_stop_event: link.is_stop_event || false,
        payload: link.payload || {},
        sourcePosition: link.source_position,
        targetPosition: link.target_position,
      },
      markerEnd: {
        type: 'arrowclosed',
      },
      style: {
        strokeWidth: 2,
        stroke: link.is_start_event ? '#22c55e' : link.is_stop_event ? '#ef4444' : '#3b82f6',
      },
    }
  })

  return { nodes: transformedNodes, edges: transformedEdges }
}

onMounted(() => {
  // Transform the NetworkX graph data into Vue Flow format
  const graphElements = transformGraph(props.graphData)

  // Use dagre to automatically layout the graph
  const dagreGraph = new dagre.graphlib.Graph()
  dagreGraph.setDefaultEdgeLabel(() => ({}))

  // Set layout direction and spacing
  dagreGraph.setGraph({
    rankdir: 'LR', // Left to right layout
    ranksep: 150, // Horizontal spacing between nodes
    nodesep: 100, // Vertical spacing between nodes
    edgesep: 80, // Edge spacing
    ranker: 'network-simplex',
  })

  // Add nodes to dagre
  graphElements.nodes.forEach((node) => {
    let width, height

    if (node.type === 'step') {
      width = 200
      height = 80
    }
    else {
      // Special nodes (Start/End)
      width = 120
      height = 60
    }

    dagreGraph.setNode(node.id, { width, height })
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

  // Set elements with calculated positions
  elements.value = [
    ...graphElements.nodes,
    ...graphElements.edges,
  ]

  // Fit the view to show all elements with some padding
  setTimeout(() => {
    fitView({ padding: 0.2 })
  }, 100)
})
</script>

<style>
.vue-flow-wrapper {
  font-family: sans-serif;
}

.step-node {
  min-width: 180px;
  min-height: 60px;
}

.special-node {
  min-width: 120px;
  min-height: 60px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.event-details-drawer {
  transition: transform 0.3s ease;
}

/* Adjust handle appearance */
.vue-flow__handle {
  width: 8px;
  height: 8px;
  border-radius: 100%;
  background-color: #555;
}

.vue-flow__handle.vue-flow__handle-connecting {
  background-color: #ff6b6b;
}

.vue-flow__handle.vue-flow__handle-valid {
  background-color: #55dd99;
}

/* Add a subtle hover effect to the edge labels */
.edge-label {
  transition: all 0.2s ease;
}

.edge-label:hover {
  transform: scale(1.1) translate(-45%, -45%);
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
}
</style>
