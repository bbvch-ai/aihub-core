import { useMutation, useQuery } from '@pinia/colada'
import { defineStore } from 'pinia'
import type { Thread } from '@core/types/thread/Thread'

export const useThreadStore = defineStore('threads', () => {
  const { getHeaders } = useAuth()

  // Fetch all threads
  const {
    data: threads,
    state: threadsLoadingState,
    refresh: refreshThreads,
    refetch: refetchThreads,
  } = useQuery<Thread[]>({
    key: ['threads'],
    staleTime: 1000 * 10, // 5 minutes
    enabled: true,
    query: () =>
      getHeaders()
        .then(headers => fetch(`/api/v1/thread/`, { headers }))
        .then(res => res.json()),
  })

  // Compute a map for easy thread lookup
  const threadMap = computed(() => {
    const map: Record<string, Thread> = {}
    threads.value?.forEach((t) => {
      map[t.id] = t
    })
    return map
  })

  // Helper to replace a thread in `threads` array after mutation
  function replaceThread(updatedThread: Thread) {
    if (!threads.value) return
    const index = threads.value.findIndex(t => t.id === updatedThread.id)
    if (index !== -1) {
      threads.value.splice(index, 1, updatedThread)
    }
    else {
      // If not found, add it (in case of newly created threads)
      threads.value.push(updatedThread)
    }
  }

  // Create a new Thread
  // Example: POST /api/v1/thread/1234 (this might vary depending on your API)
  const { mutate: createThread } = useMutation({
    mutation: async (payload: {
      id: string // according to your endpoint, it may be part of the URL
      name: string
      user_ids: string[]
      agents: { agent_id: string, agent_class: string }[]
    }) => {
      const headers = await getHeaders()
      const res = await fetch(`/api/v1/thread/${payload.id}/`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          name: payload.name,
          user_ids: payload.user_ids,
          agents: payload.agents,
        }),
      })
      if (!res.ok) {
        throw new Error(`Failed to create thread: ${res.statusText}/`)
      }
      return res.json() as Promise<Thread>
    },
    onSuccess(thread) {
      replaceThread(thread)
    },
  })

  // Get a specific thread by ID
  // Though we already have all threads, if you want to explicitly fetch one:
  const { mutate: fetchThreadById } = useMutation({
    mutation: async (id: string) => {
      const headers = await getHeaders()
      const res = await fetch(`/api/v1/thread/${id}/`, { headers })
      if (!res.ok) {
        throw new Error(`Failed to fetch thread: ${res.statusText}`)
      }
      return res.json() as Promise<Thread>
    },
    onSuccess(thread) {
      replaceThread(thread)
    },
  })

  // Add an agent to a thread
  const { mutate: addAgentToThread } = useMutation({
    mutation: async (payload: {
      threadId: string
      agent_id: string
      agent_class: string
    }) => {
      const headers = await getHeaders()
      const res = await fetch(`/api/v1/thread/${payload.threadId}/agents/`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          agent_id: payload.agent_id,
          agent_class: payload.agent_class,
        }),
      })
      if (!res.ok) {
        throw new Error(`Failed to add agent: ${res.statusText}`)
      }
      return res.json() as Promise<Thread>
    },
    onSuccess(thread) {
      replaceThread(thread)
    },
  })

  // Remove an agent from a thread
  const { mutate: removeAgentFromThread } = useMutation({
    mutation: async (payload: { threadId: string, agentId: string }) => {
      const headers = await getHeaders()
      const res = await fetch(
        `/api/v1/thread/${payload.threadId}/agents/${payload.agentId}/`,
        {
          method: 'DELETE',
          headers,
        },
      )
      if (!res.ok) {
        throw new Error(`Failed to remove agent: ${res.statusText}`)
      }
      return res.json() as Promise<Thread>
    },
    onSuccess(thread) {
      replaceThread(thread)
    },
  })

  // Add a user to a thread
  const { mutate: addUserToThread } = useMutation({
    mutation: async (payload: { threadId: string, userId: string }) => {
      const headers = await getHeaders()
      const res = await fetch(`/api/v1/thread/${payload.threadId}/users/`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ user_id: payload.userId }),
      })
      if (!res.ok) {
        throw new Error(`Failed to add user: ${res.statusText}`)
      }
      return res.json() as Promise<Thread>
    },
    onSuccess(thread) {
      replaceThread(thread)
    },
  })

  // Remove a user from a thread
  const { mutate: removeUserFromThread } = useMutation({
    mutation: async (payload: { threadId: string, userId: string }) => {
      const headers = await getHeaders()
      const res = await fetch(
        `/api/v1/thread/${payload.threadId}/users/${payload.userId}/`,
        {
          method: 'DELETE',
          headers,
        },
      )
      if (!res.ok) {
        throw new Error(`Failed to remove user: ${res.statusText}`)
      }
      return res.json() as Promise<Thread>
    },
    onSuccess(thread) {
      replaceThread(thread)
    },
  })

  return {
    threads,
    threadsLoadingState,
    refreshThreads,
    refetchThreads,
    threadMap,
    createThread,
    fetchThreadById,
    addAgentToThread,
    removeAgentFromThread,
    addUserToThread,
    removeUserFromThread,
  }
})
