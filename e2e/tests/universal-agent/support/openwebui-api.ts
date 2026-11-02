import { expect, request, type APIRequestContext } from '@playwright/test'

import { OPENWEBUI_URL } from './env'

export interface OwuiFilter {
  id: string
  name: string
}

export interface OwuiModel {
  id: string
  name?: string
  info?: { meta?: { capabilities?: Record<string, boolean>; filterIds?: string[] } } | null
  filters?: OwuiFilter[]
}

export interface OwuiSource {
  source?: { id?: string; name?: string }
  document?: string[]
  metadata?: Record<string, unknown>[]
}

export interface OwuiStatus {
  description?: string
  done?: boolean
  error?: boolean
}

export interface OwuiFile {
  type?: string
  id?: string
  name?: string
  url?: string
  content_type?: string
  size?: number
}

export interface OwuiMessage {
  id: string
  parentId: string | null
  childrenIds: string[]
  role: 'user' | 'assistant' | 'system'
  content: string
  done?: boolean
  sources?: OwuiSource[]
  statusHistory?: OwuiStatus[]
  files?: OwuiFile[]
  followUps?: string[]
}

export interface OwuiChat {
  id: string
  title: string
  chat: { history: { currentId: string | null; messages: Record<string, OwuiMessage> } }
  meta?: { tags?: string[] }
}

export interface DownloadedFile {
  contentType: string
  body: Buffer
}

/** OpenWebUI's REST API as the signed-in e2e user, with the token the browser holds in `localStorage.token`. */
export class OpenWebuiApi {
  private constructor(private readonly http: APIRequestContext) {}

  static async signedIn(token: string): Promise<OpenWebuiApi> {
    const http = await request.newContext({
      baseURL: OPENWEBUI_URL,
      ignoreHTTPSErrors: true,
      extraHTTPHeaders: { Authorization: `Bearer ${token}` },
    })
    return new OpenWebuiApi(http)
  }

  async models(refresh = false): Promise<OwuiModel[]> {
    const response = await this.http.get(`/api/models${refresh ? '?refresh=true' : ''}`)
    await expect(response, 'GET /api/models').toBeOK()
    const body = (await response.json()) as { data: OwuiModel[] }
    return body.data
  }

  async chat(chatId: string): Promise<OwuiChat> {
    const response = await this.http.get(`/api/v1/chats/${chatId}`)
    await expect(response, `GET /api/v1/chats/${chatId}`).toBeOK()
    return (await response.json()) as OwuiChat
  }

  /** The installed function ids, or null when the e2e user is no OpenWebUI admin and may not list them. */
  async functionIds(): Promise<string[] | null> {
    const response = await this.http.get('/api/v1/functions/')
    if ([401, 403].includes(response.status())) {
      return null
    }
    await expect(response, 'GET /api/v1/functions/').toBeOK()
    const functions = (await response.json()) as { id: string }[]
    return functions.map((fn) => fn.id)
  }

  async terminalServerCount(): Promise<number> {
    const response = await this.http.get('/api/v1/terminals/')
    await expect(response, 'GET /api/v1/terminals/').toBeOK()
    return ((await response.json()) as unknown[]).length
  }

  async fileContent(fileId: string): Promise<DownloadedFile> {
    const response = await this.http.get(`/api/v1/files/${fileId}/content`)
    await expect(response, `GET /api/v1/files/${fileId}/content`).toBeOK()
    return { contentType: response.headers()['content-type'] ?? '', body: await response.body() }
  }

  async dispose(): Promise<void> {
    await this.http.dispose()
  }
}
