import type { MaybeRefOrGetter } from 'vue'

/**
 * Tracks documents whose deletion has been scheduled but not yet reconciled by the pipeline.
 *
 * Deletion is eventual (the pipeline cleans the doc store + vector store ~1-3 min later), so the
 * list query keeps returning a scheduled document until cleanup completes. This module-level,
 * namespace-keyed store lets any view (list row delete or detail-page delete) mark a document as
 * scheduled and have the list hide it immediately — surviving the navigation from detail to list.
 */
const scheduledByKey = reactive(new Map<string, Set<string>>())

function keyFor(database: string, namespace: string): string {
  return `${database}/${namespace}`
}

export function useScheduledDeletions(database: MaybeRefOrGetter<string>, namespace: MaybeRefOrGetter<string>) {
  const scheduledIds = computed(() => scheduledByKey.get(keyFor(toValue(database), toValue(namespace))) ?? new Set<string>())

  function schedule(documentIds: string[]): void {
    const key = keyFor(toValue(database), toValue(namespace))
    const existing = scheduledByKey.get(key) ?? new Set<string>()
    documentIds.forEach(id => existing.add(id))
    scheduledByKey.set(key, existing)
  }

  return { scheduledIds, schedule }
}
