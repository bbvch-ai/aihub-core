<script setup lang="ts">
import Graph from 'graphology'
import forceAtlas2 from 'graphology-layout-forceatlas2'
import Sigma from 'sigma'
import { ref, onMounted, watch, onUnmounted } from 'vue'

import type { MemoryRelationDTO } from '@core/sdk/client'

interface Props {
  relations: MemoryRelationDTO[]
  selectedMemoryId?: string
}

const props = defineProps<Props>()
const emit = defineEmits<{
  selectNode: [nodeId: string]
}>()

const container = ref<HTMLDivElement>()
let sigma: Sigma | null = null
let graph: Graph | null = null

const buildGraph = () => {
  if (!props.relations || props.relations.length === 0) {
    return new Graph({ multi: true, type: 'directed' })
  }

  const g = new Graph({ multi: true, type: 'directed' })

  // Build graph from relations
  const nodeSet = new Set<string>()
  props.relations.forEach((rel) => {
    nodeSet.add(rel.source)
    nodeSet.add(rel.target)
  })

  // Add nodes with random positions
  nodeSet.forEach((node) => {
    if (!g.hasNode(node)) {
      g.addNode(node, {
        label: node,
        size: 10,
        color: '#4f46e5',
        x: Math.random(),
        y: Math.random(),
      })
    }
  })

  // Add edges
  props.relations.forEach((rel, index) => {
    g.addEdge(rel.source, rel.target, {
      label: rel.relation,
      size: 2,
      color: '#94a3b8',
    }, `edge-${index}`)
  })

  return g
}

const renderGraph = () => {
  if (!container.value) return

  // Clear previous instance
  if (sigma) {
    sigma.kill()
    sigma = null
  }

  graph = buildGraph()

  // Apply layout if graph has nodes
  if (graph.order > 0) {
    forceAtlas2.assign(graph, {
      iterations: 100,
      settings: {
        gravity: 1,
        scalingRatio: 10,
      },
    })
  }

  // Create sigma instance
  sigma = new Sigma(graph, container.value, {
    renderEdgeLabels: true,
    allowInvalidContainer: true,
  })

  // Handle node clicks
  sigma.on('clickNode', ({ node }) => {
    emit('selectNode', node)
  })

  // Highlight selected node
  if (props.selectedMemoryId && graph.hasNode(props.selectedMemoryId)) {
    graph.setNodeAttribute(props.selectedMemoryId, 'color', '#ef4444')
    graph.setNodeAttribute(props.selectedMemoryId, 'size', 15)
  }

  sigma.refresh()
}

onMounted(() => {
  renderGraph()
})

watch(() => props.relations, () => {
  renderGraph()
}, { deep: true })

watch(() => props.selectedMemoryId, (newId, oldId) => {
  if (!graph || !sigma) return

  // Reset old selection
  if (oldId && graph.hasNode(oldId)) {
    graph.setNodeAttribute(oldId, 'color', '#4f46e5')
    graph.setNodeAttribute(oldId, 'size', 10)
  }

  // Highlight new selection
  if (newId && graph.hasNode(newId)) {
    graph.setNodeAttribute(newId, 'color', '#ef4444')
    graph.setNodeAttribute(newId, 'size', 15)
  }

  sigma.refresh()
})

onUnmounted(() => {
  if (sigma) {
    sigma.kill()
  }
})
</script>

<template>
  <div
    ref="container"
    class="w-full h-full min-h-[400px]"
  />
</template>

<style scoped>
/* sigma.js renders to canvas, no additional styles needed */
</style>
