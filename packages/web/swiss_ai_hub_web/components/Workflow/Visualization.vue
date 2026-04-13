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

const COL_PITCH = NODE_WIDTH + COL_GAP
const ROW_PITCH = NODE_HEIGHT + ROW_GAP

type Adjacency = Map<string, string[]>
type GridSlot = { row: number, col: number }
type ColumnCount = 1 | 2 | 3

const chooseColumnCount = (middleCount: number): ColumnCount => {
  if (middleCount >= 12) return 3
  if (middleCount >= 6) return 2
  return 1
}

const FILL_ORDERS: Record<ColumnCount, [number[], number[]]> = {
  1: [[0], [0]],
  2: [[1, 0], [0, 1]],
  3: [[1, 0, 2], [1, 2, 0]],
}

const fillOrderForRow = (colCount: ColumnCount, row: number): number[] =>
  FILL_ORDERS[colCount][row % 2]

const buildAdjacency = (links: { source: string, target: string }[]): { children: Adjacency, parents: Adjacency } => {
  const children: Adjacency = new Map()
  const parents: Adjacency = new Map()
  for (const { source, target } of links) {
    const kids = children.get(source) ?? []
    kids.push(target)
    children.set(source, kids)
    const pars = parents.get(target) ?? []
    pars.push(source)
    parents.set(target, pars)
  }
  return { children, parents }
}

/** BFS from start nodes, yielding middle-node ids in visit order. */
const bfsMiddleOrder = (startIds: string[], middleIds: Set<string>, children: Adjacency): string[] => {
  const visited = new Set<string>(startIds)
  const order: string[] = []
  const queue = [...startIds]
  while (queue.length) {
    const current = queue.shift()!
    for (const child of children.get(current) ?? []) {
      if (visited.has(child)) continue
      visited.add(child)
      if (middleIds.has(child)) order.push(child)
      queue.push(child)
    }
  }
  return order
}

const requiredRowFor = (nodeId: string, parents: Adjacency, rowOf: Map<string, number>): number => {
  let required = 0
  for (const pid of parents.get(nodeId) ?? []) {
    const pr = rowOf.get(pid)
    if (pr !== undefined && pr + 1 > required) required = pr + 1
  }
  return required
}

const findFreeSlot = (
  fromRow: number,
  colCount: ColumnCount,
  taken: Set<string>,
): GridSlot => {
  let row = fromRow
  while (true) {
    for (const col of fillOrderForRow(colCount, row)) {
      if (!taken.has(`${row}:${col}`)) return { row, col }
    }
    row += 1
  }
}

/** Assign (row, col) slots to each middle node in BFS order. */
const assignSlots = (bfsOrder: string[], parents: Adjacency, colCount: ColumnCount): Map<string, GridSlot> => {
  const slotOf = new Map<string, GridSlot>()
  const taken = new Set<string>()
  const rowOf = new Map<string, number>()
  for (const nodeId of bfsOrder) {
    const slot = findFreeSlot(requiredRowFor(nodeId, parents, rowOf), colCount, taken)
    slotOf.set(nodeId, slot)
    rowOf.set(nodeId, slot.row)
    taken.add(`${slot.row}:${slot.col}`)
  }
  return slotOf
}

/** Column index → horizontal pixel offset. Column 1 (center in 3-col) is at x=0. */
const columnX = (colCount: ColumnCount, col: number): number => {
  if (colCount === 1) return 0
  if (colCount === 2) return (col - 0.5) * COL_PITCH
  return (col - 1) * COL_PITCH
}

/** Distribute `total` nodes horizontally around x=0. */
const centeredGroupX = (index: number, total: number): number =>
  (index - (total - 1) / 2) * COL_PITCH

/**
 * Custom layout algorithm:
 * - Start and stop nodes are centered as groups on their own rows; their x
 *   positions are independent of the column grid.
 * - Middle nodes fill 1/2/3 columns depending on middle-node count
 *   (<6 → 1 col, 6–11 → 2, 12+ → 3).
 * - Processing order: BFS from start nodes.
 * - Each node's row = min row such that all its already-placed parents have
 *   lower rows (cycles back to earlier rows are ignored).
 * - Column fill order per row: center first, then alternate sides by row parity.
 * - If a row has no free columns at the required row, bump to the next row.
 */
const layout = computed(() => {
  const { nodes: graphNodes, links } = props.graphData

  const startNodes = graphNodes.filter(n => n.type === 'start')
  const stopNodes = graphNodes.filter(n => n.type === 'stop')
  const middleNodes = graphNodes.filter(n => n.type === 'step')
  const middleIds = new Set(middleNodes.map(n => n.id))
  const colCount = chooseColumnCount(middleNodes.length)

  const { children, parents } = buildAdjacency(links)

  const bfsOrder = bfsMiddleOrder(startNodes.map(n => n.id), middleIds, children)
  // Include any middle nodes unreachable from start (defensive).
  for (const n of middleNodes) {
    if (!bfsOrder.includes(n.id)) bfsOrder.push(n.id)
  }

  const slotOf = assignSlots(bfsOrder, parents, colCount)

  const layoutMap = new Map<string, { x: number, y: number }>()
  startNodes.forEach((node, i) => {
    layoutMap.set(node.id, { x: centeredGroupX(i, startNodes.length), y: 0 })
  })
  let maxRow = -1
  middleNodes.forEach((node) => {
    const { row, col } = slotOf.get(node.id)!
    if (row > maxRow) maxRow = row
    layoutMap.set(node.id, { x: columnX(colCount, col), y: (row + 1) * ROW_PITCH })
  })
  const stopRow = maxRow + 2
  stopNodes.forEach((node, i) => {
    layoutMap.set(node.id, { x: centeredGroupX(i, stopNodes.length), y: stopRow * ROW_PITCH })
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
