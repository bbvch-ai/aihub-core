import type { OwuiMessage, OwuiSource } from './openwebui-api'

export type ToolName = 'run_command' | 'display_file' | 'read_attached_files' | 'search_knowledge'

/**
 * The pipe names a tool block by the tool's label in the run's locale (`ToolEvent.label`), so a call is recognised
 * by any of the labels the agent's translations give it, or by its raw name when the label is missing.
 */
const TOOL_LABELS: Record<ToolName, string[]> = {
  run_command: ['Run Command', 'Befehl ausführen', 'Exécuter une commande', 'Esegui comando'],
  display_file: ['Show File', 'Datei zeigen', 'Afficher un fichier', 'Mostra file'],
  read_attached_files: [
    'Read attached files',
    'Angehängte Dateien lesen',
    'Lire les fichiers joints',
    'Leggere i file allegati',
  ],
  search_knowledge: [
    'Search our knowledge',
    'Unser Wissen durchsuchen',
    'Rechercher dans nos connaissances',
    'Cercare nella nostra conoscenza',
  ],
}

export const STOPPED_EARLY_NOTICE = 'I stopped looking into this before I was done'

export interface ToolCall {
  label: string
  done: boolean
  arguments: Record<string, unknown>
  result: string | undefined
}

const TOOL_BLOCK = /<details\b[^>]*\btype="tool_calls"[^>]*>/g
const GENERATED_BLOCK = /<details\b[^>]*\btype="(?:reasoning|tool_calls|code_interpreter)"[^>]*>[\s\S]*?<\/details>/g
const HTML_ENTITIES: Record<string, string> = { '&quot;': '"', '&#x27;': "'", '&#39;': "'", '&lt;': '<', '&gt;': '>' }

/** Reads what the Universal Agent did from an assistant message of the chat JSON, never from the rendered DOM. */
export class ChatMessage {
  constructor(readonly message: OwuiMessage) {}

  get id(): string {
    return this.message.id
  }

  get toolCalls(): ToolCall[] {
    return [...this.message.content.matchAll(TOOL_BLOCK)].map(([tag]) => ChatMessage.toolCall(tag))
  }

  callsOf(tool: ToolName): ToolCall[] {
    return this.toolCalls.filter((call) => TOOL_LABELS[tool].includes(call.label) || call.label === tool)
  }

  /** The answer the user reads, without the tool and reasoning blocks around it. */
  get answer(): string {
    return this.message.content.replace(GENERATED_BLOCK, '').trim()
  }

  get sources(): OwuiSource[] {
    return this.message.sources ?? []
  }

  get sourceNames(): string[] {
    return this.sources.map((source) => source.source?.name ?? '')
  }

  /** Knowledge sources carry a document id per chunk; attached files and memories do not. */
  get knowledgeSources(): OwuiSource[] {
    return this.sources.filter((source) => (source.metadata ?? []).some((chunk) => 'document_id' in chunk))
  }

  get statusDescriptions(): string[] {
    return (this.message.statusHistory ?? []).map((status) => status.description ?? '')
  }

  get errorStatuses(): string[] {
    return (this.message.statusHistory ?? []).filter((status) => status.error).map((status) => status.description ?? '')
  }

  /** Whether the answer states `value`, however the model groups its digits (1,234 / 1'234 / 1 234). */
  mentionsNumber(value: number): boolean {
    return this.answer.replace(/(\d)[\s,'’`  ](?=\d{3}\b)/g, '$1').includes(String(value))
  }

  mentions(text: string): boolean {
    return this.answer.toLowerCase().includes(text.toLowerCase())
  }

  private static toolCall(tag: string): ToolCall {
    const attribute = (name: string): string | undefined => {
      const match = new RegExp(`\\b${name}="([^"]*)"`).exec(tag)
      return match ? ChatMessage.unescape(match[1]) : undefined
    }
    const result = attribute('result')
    return {
      label: attribute('name') ?? '',
      done: attribute('done') === 'true',
      arguments: JSON.parse(attribute('arguments') ?? '{}') as Record<string, unknown>,
      result: result === undefined ? undefined : (JSON.parse(result) as string),
    }
  }

  private static unescape(text: string): string {
    return text.replace(/&(?:quot|#x27|#39|lt|gt);/g, (entity) => HTML_ENTITIES[entity]).replace(/&amp;/g, '&')
  }
}
