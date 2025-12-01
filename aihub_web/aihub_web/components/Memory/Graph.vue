<script setup lang="ts">
import { useDark } from '@vueuse/core'
import Graph from 'graphology'
import forceAtlas2 from 'graphology-layout-forceatlas2'
import Sigma from 'sigma'
import { EdgeArrowProgram } from 'sigma/rendering'
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

const props = defineProps<Props>()
const emit = defineEmits<{
  selectNode: [nodeId: string]
}>()

const isDark = useDark({ storageKey: 'dark' })
const container = ref<HTMLDivElement>()
let sigma: Sigma | null = null
let graph: Graph | null = null

const hashString = (str: string): number => {
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i)
    hash = ((hash << 5) - hash) + char
    hash = hash & hash
  }
  return Math.abs(hash)
}

const getDeterministicPosition = (id: string, seed: 'x' | 'y'): number => {
  const hash = hashString(id + seed)
  return (hash % 1000) / 1000
}

const getCssVar = (varName: string): string => {
  if (typeof window === 'undefined') return '#000000'
  return getComputedStyle(document.documentElement).getPropertyValue(varName).trim()
}

const getColors = () => ({
  nodeActive: getCssVar('--p-primary-color'),
  nodeInactive: getCssVar('--p-surface-500'),
  nodeSelected: getCssVar('--p-red-600'),
  edgeActive: getCssVar('--p-surface-600'),
  edgeInactive: getCssVar('--p-surface-400'),
  labelColor: getCssVar('--p-primary-color'),
})

const isSearchActive = computed(() => !!props.searchResults)

const relevantNodeIds = computed(() => {
  if (!isSearchActive.value || !props.searchResults) return new Set<string>()
  const ids = new Set<string>()
  props.searchResults.memories.forEach(m => ids.add(m.id))
  props.searchResults.relations.forEach((r) => {
    ids.add(r.source)
    ids.add(r.target)
  })
  return ids
})

const relevantRelations = computed(() => {
  if (!isSearchActive.value || !props.searchResults) return new Set<string>()
  return new Set(
    props.searchResults.relations.map((r, i) => `${r.source}-${r.relation}-${r.target}-${i}`),
  )
})

interface GraphColors {
  nodeActive: string
  nodeInactive: string
  nodeSelected: string
  edgeActive: string
  edgeInactive: string
  labelColor: string
}

const buildGraph = (colors: GraphColors) => {
  if (!props.relations || props.relations.length === 0) {
    return new Graph({ multi: true, type: 'directed' })
  }

  const g = new Graph({ multi: true, type: 'directed' })

  const nodeSet = new Set<string>()
  props.relations.forEach((rel) => {
    nodeSet.add(rel.source)
    nodeSet.add(rel.target)
  })

  nodeSet.forEach((node) => {
    if (!g.hasNode(node)) {
      const isRelevant = !isSearchActive.value || relevantNodeIds.value.has(node)
      g.addNode(node, {
        label: node,
        size: isRelevant ? 10 : 8,
        color: isRelevant ? colors.nodeActive : colors.nodeInactive,
        labelColor: colors.labelColor,
        x: getDeterministicPosition(node, 'x'),
        y: getDeterministicPosition(node, 'y'),
      })
    }
  })

  props.relations.forEach((rel, index) => {
    const edgeKey = `${rel.source}-${rel.relation}-${rel.target}-${index}`
    const isRelevant = !isSearchActive.value || relevantRelations.value.has(edgeKey)
    g.addEdge(rel.source, rel.target, {
      label: rel.relation,
      size: isRelevant ? 2 : 1,
      color: isRelevant ? colors.edgeActive : colors.edgeInactive,
      labelColor: colors.labelColor,
    }, `edge-${index}`)
  })

  return g
}

const renderGraph = () => {
  if (!container.value) return

  if (sigma) {
    sigma.kill()
    sigma = null
  }

  const colors = getColors()
  graph = buildGraph(colors)

  if (graph.order > 0) {
    forceAtlas2.assign(graph, {
      iterations: 100,
      settings: {
        gravity: 1,
        scalingRatio: 10,
      },
    })
  }

  sigma = new Sigma(graph, container.value, {
    renderEdgeLabels: true,
    allowInvalidContainer: true,
    labelColor: { attribute: 'labelColor', color: colors.labelColor },
    edgeLabelColor: { attribute: 'labelColor', color: colors.labelColor },
    edgeProgramClasses: {
      arrow: EdgeArrowProgram,
    },
    defaultEdgeType: 'arrow',
  })

  sigma.on('clickNode', ({ node }) => {
    emit('selectNode', node)
  })

  if (props.selectedMemoryId && graph.hasNode(props.selectedMemoryId)) {
    graph.setNodeAttribute(props.selectedMemoryId, 'color', colors.nodeSelected)
    graph.setNodeAttribute(props.selectedMemoryId, 'size', 15)
  }

  sigma.refresh()
}

onMounted(() => {
  renderGraph()
})

watch(() => [props.relations, props.searchResults], () => {
  renderGraph()
}, { deep: true })

watch(() => props.selectedMemoryId, (newId, oldId) => {
  if (!graph || !sigma) return

  const colors = getColors()

  if (oldId && graph.hasNode(oldId)) {
    const isRelevant = !isSearchActive.value || relevantNodeIds.value.has(oldId)
    graph.setNodeAttribute(oldId, 'color', isRelevant ? colors.nodeActive : colors.nodeInactive)
    graph.setNodeAttribute(oldId, 'size', isRelevant ? 10 : 8)
  }

  if (newId && graph.hasNode(newId)) {
    graph.setNodeAttribute(newId, 'color', colors.nodeSelected)
    graph.setNodeAttribute(newId, 'size', 15)
  }

  sigma.refresh()
})

watch(isDark, async () => {
  await nextTick()
  renderGraph()
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
    class="size-full min-h-[400px]"
  />
</template>

<style scoped>
/* sigma.js renders to canvas, no additional styles needed */
</style>
