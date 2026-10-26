import { DOCUMENT_COLLECTION, DOCUMENT_DATABASE, DOCUMENT_GLOB, TASK_LLM } from './env'

/** The settings that point a profile at the seeded documents: one collection, the path filter and the extraction model. */
export class DocumentProfile {
  static configuration(collection = DOCUMENT_COLLECTION, glob = DOCUMENT_GLOB): Record<string, unknown> {
    return {
      knowledge_tool: {
        every_readable_collection: false,
        sources: [
          {
            vector_store: {
              collection_name: DOCUMENT_DATABASE,
              all_namespaces: false,
              index_namespaces: [collection],
            },
          },
        ],
      },
      knowledge_documents: { enabled: true, path_glob: glob },
      record_extraction: {
        extraction_model_name: TASK_LLM,
        max_files: 100,
        minutes_per_turn: 5,
        max_documents_total: 1000,
        max_rows: 500,
        max_document_chars: 500_000,
        max_parallel_extractions: 4,
      },
    }
  }

  /** The rows of the markdown tables in an answer, without their header and separator lines. */
  static tableRows(answer: string): string[] {
    const lines = answer.split('\n').filter((line) => line.trim().startsWith('|'))
    return lines.filter((line, index) => index > 0 && !/^\|\s*-{3}/.test(line) && !/^\|\s*-{3}/.test(lines[index + 1] ?? ''))
  }
}
