<template>
  <ProgressBar
    v-if="threadIsLoading || threadEventsAreLoading || !thread || !threadEvents"
    mode="indeterminate"
    style="height: 2px"
  />
  <div
    v-else
    ref="threadPanelRef"
    class="relative h-[calc(100vh-50px)] w-1/2 min-w-[800px] overflow-y-auto border-l border-surface-200 p-3 dark:border-surface-700"
  >
    <div class="flex flex-col gap-4">
      <div class="flex items-center gap-2 p-3">
        <ToggleSwitch
          v-model="showInactive"
        />
        <p class="text-sm opacity-60">
          Show Unused Nodes
        </p>
      </div>
      <div
        v-for="(docInfo, docId) in documentMap"
        :key="docId"
      >
        <KnowledgeDocumentWithNodes
          :db="docInfo.db"
          :namespace="docInfo.namespace"
          :document-id="docInfo.id"
          :input-nodes="docInfo.nodes"
          :show-inactive="showInactive"
        />
      </div>
    </div>
    <div
      class="fixed top-1/2 -translate-y-1/2"
      :style="{ left: `${panelLeftPosition - 16}px` }"
    >
      <i
        class="pi pi-chevron-right cursor-pointer rounded-full border border-surface-200 bg-surface-0 p-3 hover:bg-surface-100 dark:border-surface-700 dark:bg-surface-900 hover:dark:bg-surface-800"
        @click="closeSources"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import type { AgentEventReadable, RetrieverEventReadable, IngestedNode } from '@core/sdk/client'

const route = useRoute()
const router = useRouter()
const localeRoute = useLocaleRoute()

const showInactive = ref<boolean>(false)
const threadPanelRef = ref(null)
const panelBounding = useElementBounding(threadPanelRef)
const panelLeftPosition = computed(() => panelBounding.left.value)

const { thread, threadIsLoading } = useThread()
const { threadEvents, threadEventsAreLoading } = useThreadEvents()

const closeSources = () => {
  router.push(localeRoute('/service/openai'))
}

const retrieveEvents = computed<AgentEventReadable[]>(() => {
  return threadEvents.value?.filter((event: AgentEventReadable) => {
    return event.display_id === route.params.display_id && event.event.nodes
  })
})

type DocumentInfo = {
  db: string
  namespace: string
  id: string
  nodes: IngestedNode[]
}

const extractBucket = (source: string): string => {
  const match = source.match(/(?:s3:\/\/|^\/)([^/]+)/)
  return match?.[1] ?? ''
}

const documentMap = computed<Record<string, DocumentInfo>>(() => {
  const docs: Record<string, DocumentInfo> = {}
  retrieveEvents.value?.forEach((event: AgentEventReadable & { event: RetrieverEventReadable }) => {
    (event.event.nodes ?? []).forEach((node: IngestedNode) => {
      if (!(node.document_id in docs)) {
        docs[node.document_id] = {
          db: extractBucket(node.source),
          namespace: node.namespace,
          id: node.document_id,
          nodes: [],
        }
      }
      docs[node.document_id].nodes.push(node)
    })
  })
  return docs
})
</script>
