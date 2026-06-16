import { useStorage } from '@vueuse/core'

import type { MaybeRefOrGetter } from 'vue'

/**
 * Tracks documents whose deletion has been scheduled but not yet reconciled by the pipeline.
 *
 * Deletion is eventual: the API removes the S3 source immediately and returns 202, but the doc
 * store + vector store are only cleaned by the pipeline a few minutes later. Until then the list
 * query keeps returning the document. Rather than optimistically hiding it (which flickers back on
 * a page refresh once the in-memory state is lost), we persist scheduled ids in localStorage and
 * render a "Deleting" badge. The row disappears for good once the pipeline removes it and the list
 * refetches. Entries auto-expire after a TTL so a failed cleanup eventually re-surfaces the row
 * instead of hiding the truth forever.
 */
const TTL_MS = 30 * 60 * 1000

const store = useStorage<Record<string, number>>('aihub:scheduled-deletions', {})

function entryKey(database: string, namespace: string, documentId: string): string {
  return `${database}/${namespace}/${documentId}`
}

export function useScheduledDeletions(database: MaybeRefOrGetter<string>, namespace: MaybeRefOrGetter<string>) {
  function isScheduled(documentId: string): boolean {
    const scheduledAt = store.value[entryKey(toValue(database), toValue(namespace), documentId)]
    return scheduledAt != null && Date.now() - scheduledAt < TTL_MS
  }

  function schedule(documentIds: string[]): void {
    const now = Date.now()
    const next: Record<string, number> = {}
    // Drop expired entries while we rewrite, keeping localStorage bounded.
    for (const [key, scheduledAt] of Object.entries(store.value)) {
      if (now - scheduledAt < TTL_MS) {
        next[key] = scheduledAt
      }
    }
    for (const documentId of documentIds) {
      next[entryKey(toValue(database), toValue(namespace), documentId)] = now
    }
    store.value = next
  }

  return { isScheduled, schedule }
}
