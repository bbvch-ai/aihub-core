<template>
  <div
    ref="container"
    class="size-full min-h-[400px]"
  />
</template>

<script setup lang="ts">
import { useDark } from '@vueuse/core'
import Graph from 'graphology'
import forceAtlas2 from 'graphology-layout-forceatlas2'
import Sigma from 'sigma'
import { createEdgeArrowProgram } from 'sigma/rendering'
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'

import type { MemoryDto, MemoryRelationDto } from '@core/sdk/client'

interface Props {
  relations: MemoryRelationDto[]
  selectedMemoryId?: string
  searchResults?: {
    memories: MemoryDto[]
    relations: MemoryRelationDto[]
  } | null
}

interface Colors {
  nodeActive: string
  nodeInactive: string
  nodeSelected: string
  edgeActive: string
  edgeInactive: string
  labelColor: string
}

const props = defineProps<Props>()
const emit = defineEmits<{ selectNode: [nodeId: string] }>()

const isDark = useDark({ storageKey: 'dark' })
const container = ref<HTMLDivElement>()

let sigma: Sigma | null = null
let graph: Graph | null = null

const MIN_NODE_SIZE = 10
const MAX_NODE_SIZE = 50

const CustomArrowProgram = createEdgeArrowProgram({
  widenessToThicknessRatio: 3,
  lengthToThicknessRatio: 4,
})

const isSearchActive = computed(() => !!props.searchResults)

const relevantNodeIds = computed(() => {
  if (!props.searchResults) return new Set<string>()
  const ids = new Set<string>()
  props.searchResults.memories.forEach(m => ids.add(m.id))
  props.searchResults.relations.forEach((r) => {
    ids.add(r.source)
    ids.add(r.target)
  })
  return ids
})

const relevantRelationKeys = computed(() => {
  if (!props.searchResults) return new Set<string>()
  return new Set(
    props.searchResults.relations.map((r, i) => `${r.source}-${r.relation}-${r.target}-${i}`),
  )
})

const hashString = (str: string): number => {
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    hash = ((hash << 5) - hash) + str.charCodeAt(i)
    hash = hash & hash
  }
  return Math.abs(hash)
}

const getDeterministicPosition = (id: string, seed: string): number => {
  return (hashString(id + seed) % 1000) / 1000
}

const getCssVar = (varName: string): string => {
  if (typeof window === 'undefined') return '#000000'
  return getComputedStyle(document.documentElement).getPropertyValue(varName).trim()
}

const getColors = (): Colors => ({
  nodeActive: getCssVar('--p-primary-color'),
  nodeInactive: getCssVar('--p-surface-500'),
  nodeSelected: getCssVar('--p-red-600'),
  edgeActive: getCssVar('--p-surface-600'),
  edgeInactive: getCssVar('--p-surface-400'),
  labelColor: getCssVar('--p-primary-color'),
})

const isNodeRelevant = (nodeId: string): boolean => {
  return !isSearchActive.value || relevantNodeIds.value.has(nodeId)
}

const isEdgeRelevant = (edgeKey: string): boolean => {
  return !isSearchActive.value || relevantRelationKeys.value.has(edgeKey)
}

const lerp = (min: number, max: number, t: number): number => {
  return min + t * (max - min)
}

const calculateNodeSize = (degree: number, minDegree: number, maxDegree: number): number => {
  if (maxDegree === minDegree) return (MIN_NODE_SIZE + MAX_NODE_SIZE) / 2
  const t = (degree - minDegree) / (maxDegree - minDegree)
  return lerp(MIN_NODE_SIZE, MAX_NODE_SIZE, t)
}

const buildGraph = (colors: Colors): Graph => {
  const g = new Graph({ multi: true, type: 'directed' })

  if (!props.relations?.length) return g

  const nodeSet = new Set<string>()
  props.relations.forEach((rel) => {
    nodeSet.add(rel.source)
    nodeSet.add(rel.target)
  })

  nodeSet.forEach((node) => {
    g.addNode(node, {
      label: node,
      x: getDeterministicPosition(node, 'x'),
      y: getDeterministicPosition(node, 'y'),
    })
  })

  props.relations.forEach((rel, index) => {
    const edgeKey = `${rel.source}-${rel.relation}-${rel.target}-${index}`
    const relevant = isEdgeRelevant(edgeKey)
    g.addEdge(rel.source, rel.target, {
      label: rel.relation,
      size: relevant ? 4 : 2,
      color: relevant ? colors.edgeActive : colors.edgeInactive,
      labelColor: colors.labelColor,
    }, `edge-${index}`)
  })

  const degrees = g.mapNodes(node => g.degree(node))
  const minDegree = Math.min(...degrees)
  const maxDegree = Math.max(...degrees)

  g.forEachNode((node) => {
    const degree = g.degree(node)
    const size = calculateNodeSize(degree, minDegree, maxDegree)
    const relevant = isNodeRelevant(node)

    g.setNodeAttribute(node, 'baseSize', size)
    g.setNodeAttribute(node, 'size', size)
    g.setNodeAttribute(node, 'color', relevant ? colors.nodeActive : colors.nodeInactive)
    g.setNodeAttribute(node, 'labelColor', colors.labelColor)
  })

  return g
}

const applyLayout = (g: Graph): void => {
  if (g.order === 0) return
  forceAtlas2.assign(g, {
    iterations: 100,
    settings: { gravity: 1, scalingRatio: 10 },
  })
}

const highlightSelectedNode = (nodeId: string | undefined, colors: Colors): void => {
  if (!graph || !nodeId || !graph.hasNode(nodeId)) return
  graph.setNodeAttribute(nodeId, 'color', colors.nodeSelected)
}

const renderGraph = (): void => {
  if (!container.value) return

  sigma?.kill()
  sigma = null

  const colors = getColors()
  graph = buildGraph(colors)
  applyLayout(graph)

  sigma = new Sigma(graph, container.value, {
    renderEdgeLabels: true,
    allowInvalidContainer: true,
    labelColor: { attribute: 'labelColor', color: colors.labelColor },
    edgeLabelColor: { attribute: 'labelColor', color: colors.labelColor },
    edgeProgramClasses: { arrow: CustomArrowProgram },
    defaultEdgeType: 'arrow',
  })

  sigma.on('clickNode', ({ node }) => emit('selectNode', node))

  highlightSelectedNode(props.selectedMemoryId, colors)
  sigma.refresh()
}

watch(
  () => [props.relations, props.searchResults],
  () => renderGraph(),
  { deep: true },
)

watch(
  () => props.selectedMemoryId,
  (newId, oldId) => {
    if (!graph || !sigma) return

    const colors = getColors()

    if (oldId && graph.hasNode(oldId)) {
      const baseSize = graph.getNodeAttribute(oldId, 'baseSize') as number
      graph.setNodeAttribute(oldId, 'size', baseSize)
      graph.setNodeAttribute(oldId, 'color', isNodeRelevant(oldId) ? colors.nodeActive : colors.nodeInactive)
    }

    highlightSelectedNode(newId, colors)
    sigma.refresh()
  },
)

watch(isDark, async () => {
  await nextTick()
  renderGraph()
})

onMounted(() => renderGraph())
onUnmounted(() => sigma?.kill())
</script>
