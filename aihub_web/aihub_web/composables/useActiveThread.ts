import { useThread } from '@core/composables/useThread'
import { useLocalePath } from '#i18n'

export const useActiveThread = () => {
  const route = useRoute()
  const router = useRouter()
  const localePath = useLocalePath()

  const getActiveThread = () => {
    const threadId = route.params.id
    if (!threadId) {
      return null
    }
    return useThread(threadId)
  }

  const setActiveThread = (threadId: string) => {
    router.push(localePath({ name: 'thread-id', params: { id: threadId } }))
  }

  const activeThreadId = computed<string>({
    get(): string {
      const id = route.params.id
      return Array.isArray(id) ? id[0] : id
    },
    set(threadId: string) {
      setActiveThread(threadId)
    },
  })

  return {
    getActiveThread,
    setActiveThread,
    activeThreadId,
  }
}
