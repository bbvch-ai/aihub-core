import type { Agent } from 'node:http'
import type { User } from 'oidc-client-ts'

export interface ThreadResponse {
  id: string
  name: string
  users: User[]
  agents: Agent[]
}
