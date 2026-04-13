<template>
  <VueFlow
    :nodes="nodes"
    :edges="edges"
    :min-zoom="0.2"
    :max-zoom="4"
    :nodes-connectable="false"
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
import { Background } from '@vue-flow/background'
import { VueFlow, MarkerType, Position, useVueFlow } from '@vue-flow/core'
import { computed, onMounted } from 'vue'

import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'

import type { WorkflowGraph } from '@core/sdk/client'

const NODE_WIDTH = 298
const NODE_HEIGHT = 100
const ROW_GAP = 80
const COL_GAP = 80

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

/**
 * Custom layout algorithm:
 * - Start and stop nodes are centered as groups on their own rows; their x
 *   positions are independent of the column grid.
 * - Middle nodes fill 1/2/3 columns depending on middle-node count
 *   (<6 → 1 col, 6–11 → 2, 12+ → 3).
 * - Processing order: BFS from start nodes.
 * - Each node's row = min row such that all its already-placed parents have
 *   lower rows (cycles back to earlier rows are ignored).
 * - Column fill order per row:
 *     1 col  → [0]
 *     2 cols → even rows [1, 0] (right→left), odd rows [0, 1] (left→right)
 *     3 cols → even rows [1, 0, 2] (center→left→right), odd rows [1, 2, 0]
 * - If a row has no free columns at the required row, bump to the next row.
 */
const layout = computed(() => {
  const { nodes: graphNodes, links } = props.graphData

  const startNodes = graphNodes.filter(n => n.type === 'start')
  const stopNodes = graphNodes.filter(n => n.type === 'stop')
  const middleNodes = graphNodes.filter(n => n.type === 'step')

  const colCount = middleNodes.length >= 12 ? 3 : middleNodes.length >= 6 ? 2 : 1

  const childrenOf = new Map<string, string[]>()
  const parentsOf = new Map<string, string[]>()
  for (const link of links) {
    const kids = childrenOf.get(link.source) ?? []
    kids.push(link.target)
    childrenOf.set(link.source, kids)
    const pars = parentsOf.get(link.target) ?? []
    pars.push(link.source)
    parentsOf.set(link.target, pars)
  }

  // BFS from start nodes → ordered list of middle nodes (excluding start/stop).
  const middleIds = new Set(middleNodes.map(n => n.id))
  const visited = new Set<string>()
  const bfsOrder: string[] = []
  const queue: string[] = startNodes.map(n => n.id)
  startNodes.forEach(n => visited.add(n.id))
  while (queue.length) {
    const current = queue.shift()!
    for (const child of childrenOf.get(current) ?? []) {
      if (visited.has(child)) continue
      visited.add(child)
      if (middleIds.has(child)) bfsOrder.push(child)
      queue.push(child)
    }
  }
  // Any middle nodes not reachable from start (shouldn't happen, but be safe).
  for (const n of middleNodes) {
    if (!bfsOrder.includes(n.id)) bfsOrder.push(n.id)
  }

  const fillOrderForRow = (row: number): number[] => {
    if (colCount === 1) return [0]
    if (colCount === 2) return row % 2 === 0 ? [1, 0] : [0, 1]
    return row % 2 === 0 ? [1, 0, 2] : [1, 2, 0]
  }

  const rowOf = new Map<string, number>()
  const colOf = new Map<string, number>()
  const slotKey = (r: number, c: number) => `${r}:${c}`
  const takenSlots = new Set<string>()

  for (const nodeId of bfsOrder) {
    let requiredRow = 0
    for (const pid of parentsOf.get(nodeId) ?? []) {
      const pr = rowOf.get(pid)
      if (pr !== undefined && pr + 1 > requiredRow) requiredRow = pr + 1
    }
    let placed = false
    for (let r = requiredRow; !placed; r++) {
      for (const c of fillOrderForRow(r)) {
        if (!takenSlots.has(slotKey(r, c))) {
          rowOf.set(nodeId, r)
          colOf.set(nodeId, c)
          takenSlots.add(slotKey(r, c))
          placed = true
          break
        }
      }
    }
  }

  const colPitch = NODE_WIDTH + COL_GAP
  const rowPitch = NODE_HEIGHT + ROW_GAP

  // Column → visual x. col 1 (or col 0 in 1-col mode) is the center.
  const colToX = (col: number): number => {
    if (colCount === 1) return 0
    if (colCount === 2) return (col - 0.5) * colPitch
    return (col - 1) * colPitch
  }

  // Evenly distribute a centered group of n nodes horizontally.
  const centeredGroupX = (index: number, total: number): number =>
    (index - (total - 1) / 2) * colPitch

  const layoutMap = new Map<string, { x: number, y: number }>()

  // Start nodes on row 0, middle nodes on rows 1..maxRow+1, stop nodes below.
  startNodes.forEach((node, i) => {
    layoutMap.set(node.id, { x: centeredGroupX(i, startNodes.length), y: 0 })
  })
  let maxMiddleRow = -1
  middleNodes.forEach((node) => {
    const r = rowOf.get(node.id)!
    const c = colOf.get(node.id)!
    if (r > maxMiddleRow) maxMiddleRow = r
    layoutMap.set(node.id, { x: colToX(c), y: (r + 1) * rowPitch })
  })
  const stopRow = maxMiddleRow + 2
  stopNodes.forEach((node, i) => {
    layoutMap.set(node.id, { x: centeredGroupX(i, stopNodes.length), y: stopRow * rowPitch })
  })

  return layoutMap
})

const nodes = computed(() => props.graphData.nodes.map((node) => {
  const pos = layout.value.get(node.id)!
  return {
    id: node.id,
    type: node.type,
    position: pos,
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

<style>
/* Selected nodes: bolder red border + red glow so even start/end nodes
 * (already red) stand out clearly. */
.vue-flow__node.selected > * {
  border-color: rgb(239 68 68) !important; /* red-500 */
  background-color: oklch(88.5% 0.062 18.334) !important; /* red-100 */
}
.dark .vue-flow__node.selected > * {
  background-color: oklch(25.8% 0.092 26.042) !important;
}
.vue-flow__edge.selected .vue-flow__edge-path {
  stroke: rgb(239 68 68) !important;
  stroke-width: 2 !important;
}
</style>
