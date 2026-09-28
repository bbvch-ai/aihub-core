import { useDocumentVisibility, useIntervalFn } from '@vueuse/core'

import type { DocumentDto } from '@core/sdk/client'
import type { MaybeRefOrGetter } from 'vue'

// Ingestion runs asynchronously in Dagster and nothing pushes its completion to the UI, so a freshly uploaded
// document would stay "Processing" until the next focus or remount. Polling runs only while a row on the page is
// still pending and the tab is visible, so a fully ingested page costs nothing.
const INGESTION_POLL_INTERVAL_MS = 5_000

export function useDocumentIngestionPolling(
  documents: MaybeRefOrGetter<DocumentDto[]>,
  refetch: () => Promise<unknown>,
) {
  const route = useRoute()
  const { tenantId } = useTenant()
  const queryCache = useQueryCache()
  const visibility = useDocumentVisibility()

  const pendingIds = computed(() => new Set(
    toValue(documents).filter(document => !document.is_ingested).map(document => document.id),
  ))

  const { pause, resume } = useIntervalFn(() => refetch(), INGESTION_POLL_INTERVAL_MS, { immediate: false })

  watch(
    [() => pendingIds.value.size > 0, visibility],
    ([hasPendingDocuments, visibilityState]) => {
      if (hasPendingDocuments && visibilityState === 'visible') {
        resume()
      }
      else {
        pause()
      }
    },
    { immediate: true },
  )

  // The detail, nodes and summary queries of a document share its key prefix and are cached for minutes, so an
  // open detail view would keep showing the pre-ingestion state without this.
  watch(pendingIds, (currentPendingIds, previousPendingIds) => {
    const ingestedIds = toValue(documents)
      .filter(document => document.is_ingested && previousPendingIds?.has(document.id) && !currentPendingIds.has(document.id))
      .map(document => document.id)
    for (const documentId of ingestedIds) {
      queryCache.invalidateQueries({
        key: ['tenant', tenantId.value, 'knowledge', 'databases', route.params.db as string, 'namespaces', route.params.namespace as string, 'documents', documentId],
      })
    }
  })
}
