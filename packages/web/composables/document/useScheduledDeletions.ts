import { useStorage } from '@vueuse/core'

import type { MaybeRefOrGetter } from 'vue'

// Deletion is eventual (the pipeline cleans the stores well after the API returns), so the list keeps
// returning a deleted document for a while. We persist scheduled ids in localStorage — surviving page
// refreshes — to drive a "Deleting" badge, and expire them after a TTL so a failed cleanup eventually
// re-surfaces the row instead of hiding it forever.
//
// The TTL has to cover a Dagster backlog, not just a slow run: the cleanup waits on a NATS sensor tick,
// then the observe job's turn in the queue, then a run-status sensor tick, then the remove job's turn.
// A busy instance can push that out for hours, so a day is the honest bound.
const TTL_MS = 24 * 60 * 60 * 1000

const store = useStorage<Record<string, number>>('aihub:scheduled-deletions', {})

function entryKey(database: string, namespace: string, documentId: string): string {
  return `${database}/${namespace}/${documentId}`
}

export function useScheduledDeletions(database: MaybeRefOrGetter<string>, namespace: MaybeRefOrGetter<string>) {
  function scheduledAt(documentId: string): number | undefined {
    const at = store.value[entryKey(toValue(database), toValue(namespace), documentId)]
    return at != null && Date.now() - at < TTL_MS ? at : undefined
  }

  function isScheduled(documentId: string): boolean {
    return scheduledAt(documentId) != null
  }

  function schedule(documentIds: string[]): void {
    const now = Date.now()
    const next: Record<string, number> = {}
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

  function unschedule(documentIds: string[]): void {
    const keysToRemove = new Set(
      documentIds.map(documentId => entryKey(toValue(database), toValue(namespace), documentId)),
    )
    const remaining = Object.entries(store.value).filter(([key]) => !keysToRemove.has(key))
    if (remaining.length !== Object.keys(store.value).length) {
      store.value = Object.fromEntries(remaining)
    }
  }

  return { isScheduled, scheduledAt, schedule, unschedule }
}
