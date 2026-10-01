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
  isFetching: MaybeRefOrGetter<boolean>,
) {
  const route = useRoute()
  const { tenantId } = useTenant()
  const queryCache = useQueryCache()
  const visibility = useDocumentVisibility()
  const { isScheduled } = useScheduledDeletions(
    () => route.params.db as string,
    () => route.params.namespace as string,
  )

  // A row being deleted never becomes ingested and its cleanup can take hours, so it must not keep the page polling.
  const pendingIds = computed(() => new Set(
    toValue(documents)
      .filter(document => !document.is_ingested && !isScheduled(document.id))
      .map(document => document.id),
  ))

  // refetch() aborts the request still in flight, so a list slower than the interval would never land. Skipping the
  // tick lets it finish instead.
  const { pause, resume } = useIntervalFn(() => {
    if (!toValue(isFetching)) {
      refetch()
    }
  }, INGESTION_POLL_INTERVAL_MS, { immediate: false })

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

  // The detail, nodes and summary queries of a document share its key prefix and are cached for minutes, so an open
  // detail view would keep showing the pre-ingestion state without this. A document that left the page before we saw
  // it finish is refreshed too; invalidating one that is gone is harmless.
  watch(pendingIds, (currentPendingIds, previousPendingIds) => {
    const settledIds = [...(previousPendingIds ?? [])].filter(documentId => !currentPendingIds.has(documentId))
    for (const documentId of settledIds) {
      queryCache.invalidateQueries({
        key: ['tenant', tenantId.value, 'knowledge', 'databases', route.params.db as string, 'namespaces', route.params.namespace as string, 'documents', documentId],
      })
    }
  })
}
