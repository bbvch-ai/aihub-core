import { getImage } from '@core/sdk/client'

import type { MaybeRefOrGetter } from 'vue'

const STORED_IMAGE = /^s3:\/\/agent-files\/([^/]+)\/([^/]+)\/images\/([^/]+)$/

/**
 * A URL an `<img>` can show for an image block. Images sent to an agent are stored and referenced as
 * `s3://agent-files/…`, which a browser cannot load and which needs the user's token, so they are fetched through
 * the API and shown from a blob URL. Any other URL is returned as it is.
 */
export const useStoredImageUrl = (url: MaybeRefOrGetter<string | null | undefined>) => {
  const { tenantId } = useTenant()
  const src = ref<string>()
  let objectUrl: string | undefined

  const release = () => {
    if (objectUrl) URL.revokeObjectURL(objectUrl)
    objectUrl = undefined
  }

  type Source = [string | null | undefined, string | null | undefined]
  watch((): Source => [toValue(url), tenantId.value], async ([current, tenant]: Source) => {
    release()
    const stored = current?.match(STORED_IMAGE)
    if (!stored) {
      src.value = current ?? undefined
      return
    }
    src.value = undefined
    if (!tenant) return
    const [, agentClass, agentId, name] = stored
    const blob = await getImage({
      composable: '$fetch',
      path: { tenant_id: tenant, agent_class: agentClass!, agent_id: agentId!, name: name! },
      responseType: 'blob',
    }) as Blob
    objectUrl = URL.createObjectURL(blob)
    src.value = objectUrl
  }, { immediate: true })

  onBeforeUnmount(release)

  return { src }
}
