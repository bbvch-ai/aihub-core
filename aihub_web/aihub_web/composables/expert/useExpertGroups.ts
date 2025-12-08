import {
  getGroups,
  getGroup,
  createGroup,
  updateGroup,
  deleteGroup,
  addMember,
  removeMember,
} from '@core/sdk/client'

import type { ExpertGroupResponse, CreateExpertGroupRequest, UpdateExpertGroupRequest } from '@core/sdk/client'

export const useExpertGroups = () => {
  const config = useRuntimeConfig()
  const apiBase = config.public.apiUrl || '/api/v1'
  const { getHeaders } = useAuth()

  const query = useQuery<ExpertGroupResponse[]>({
    key: ['expert-groups'],
    query: async () => {
      const headers = await getHeaders()
      return await getGroups({
        composable: '$fetch',
        baseUrl: apiBase,
        headers,
      })
    },
  })

  const groups = computed(() => query.data.value ?? [])

  return {
    groups,
    isLoading: query.isPending,
    refetch: query.refetch,
  }
}

export const useExpertGroup = (groupId: Ref<string>) => {
  const config = useRuntimeConfig()
  const apiBase = config.public.apiUrl || '/api/v1'
  const { getHeaders } = useAuth()

  const query = useQuery<ExpertGroupResponse>({
    key: () => ['expert-groups', groupId.value],
    query: async () => {
      const headers = await getHeaders()
      return await getGroup({
        composable: '$fetch',
        baseUrl: apiBase,
        path: { group_id: groupId.value },
        headers,
      })
    },
  })

  const group = computed(() => query.data.value)

  return {
    group,
    isLoading: query.isPending,
    refetch: query.refetch,
  }
}

export const useCreateExpertGroup = () => {
  const queryCache = useQueryCache()
  const config = useRuntimeConfig()
  const apiBase = config.public.apiUrl || '/api/v1'
  const { getHeaders } = useAuth()

  const { mutate, mutateAsync, isPending } = useMutation({
    mutation: async (groupData: CreateExpertGroupRequest) => {
      const headers = await getHeaders()
      const result = await createGroup({
        composable: '$fetch',
        baseUrl: apiBase,
        body: groupData,
        headers,
      })
      queryCache.invalidateQueries({ key: ['expert-groups'] })
      return result
    },
  })

  return { createGroup: mutate, createGroupAsync: mutateAsync, isPending }
}

export const useUpdateExpertGroup = () => {
  const queryCache = useQueryCache()
  const config = useRuntimeConfig()
  const apiBase = config.public.apiUrl || '/api/v1'
  const { getHeaders } = useAuth()

  const { mutate, mutateAsync, isPending } = useMutation({
    mutation: async (params: { groupId: string, groupData: UpdateExpertGroupRequest }) => {
      const headers = await getHeaders()
      const result = await updateGroup({
        composable: '$fetch',
        baseUrl: apiBase,
        path: { group_id: params.groupId },
        body: params.groupData,
        headers,
      })
      queryCache.invalidateQueries({ key: ['expert-groups'] })
      queryCache.invalidateQueries({ key: ['expert-groups', params.groupId] })
      return result
    },
  })

  return { updateGroup: mutate, updateGroupAsync: mutateAsync, isPending }
}

export const useDeleteExpertGroup = () => {
  const queryCache = useQueryCache()
  const config = useRuntimeConfig()
  const apiBase = config.public.apiUrl || '/api/v1'
  const { getHeaders } = useAuth()

  const { mutate, mutateAsync, isPending } = useMutation({
    mutation: async (groupId: string) => {
      const headers = await getHeaders()
      await deleteGroup({
        composable: '$fetch',
        baseUrl: apiBase,
        path: { group_id: groupId },
        headers,
      })
      queryCache.invalidateQueries({ key: ['expert-groups'] })
    },
  })

  return { deleteGroup: mutate, deleteGroupAsync: mutateAsync, isPending }
}

export const useAddGroupMember = () => {
  const queryCache = useQueryCache()
  const config = useRuntimeConfig()
  const apiBase = config.public.apiUrl || '/api/v1'
  const { getHeaders } = useAuth()

  const { mutate, mutateAsync, isPending } = useMutation({
    mutation: async (params: { groupId: string, userId: string }) => {
      const headers = await getHeaders()
      const result = await addMember({
        composable: '$fetch',
        baseUrl: apiBase,
        path: { group_id: params.groupId, user_id: params.userId },
        headers,
      })
      queryCache.invalidateQueries({ key: ['expert-groups'] })
      queryCache.invalidateQueries({ key: ['expert-groups', params.groupId] })
      return result
    },
  })

  return { addMember: mutate, addMemberAsync: mutateAsync, isPending }
}

export const useRemoveGroupMember = () => {
  const queryCache = useQueryCache()
  const config = useRuntimeConfig()
  const apiBase = config.public.apiUrl || '/api/v1'
  const { getHeaders } = useAuth()

  const { mutate, mutateAsync, isPending } = useMutation({
    mutation: async (params: { groupId: string, userId: string }) => {
      const headers = await getHeaders()
      const result = await removeMember({
        composable: '$fetch',
        baseUrl: apiBase,
        path: { group_id: params.groupId, user_id: params.userId },
        headers,
      })
      queryCache.invalidateQueries({ key: ['expert-groups'] })
      queryCache.invalidateQueries({ key: ['expert-groups', params.groupId] })
      return result
    },
  })

  return { removeMember: mutate, removeMemberAsync: mutateAsync, isPending }
}
