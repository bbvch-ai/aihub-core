/**
 * Where the OpenWebUI and AI-Hub specs run, read once from the environment. The defaults target the build stack
 * behind Traefik; README.md lists the values for the dev stack.
 */

const DOMAIN = process.env.E2E_DOMAIN ?? '127.0.0.1.nip.io'

export const OPENWEBUI_URL = (process.env.E2E_OPENWEBUI_URL ?? `https://openwebui.${DOMAIN}`).replace(/\/$/, '')
export const API_URL = (process.env.E2E_API_URL ?? `https://${DOMAIN}/api/v1`).replace(/\/$/, '')
export const TENANT = process.env.E2E_TENANT ?? 'default'
export const API_TOKEN = process.env.E2E_API_TOKEN ?? ''

export const OPENWEBUI_EMAIL = process.env.E2E_OPENWEBUI_EMAIL ?? 'e2e-test@swiss-ai-hub.ch'
export const OPENWEBUI_PASSWORD = process.env.E2E_OPENWEBUI_PASSWORD ?? 'e2e-test-password'

export const UNIVERSAL_AGENT_CLASS = 'UniversalAgent'
export const KNOWLEDGE_EXTRACTION_AGENT_CLASS = 'KnowledgeExtractionAgent'
export const AGENT_MODEL_PREFIX = 'aihub-pipeline.'
export const TEMPLATE_PROFILE = process.env.E2E_UNIVERSAL_AGENT_TEMPLATE ?? 'workplace-assistant'
export const MAIN_LLM = process.env.E2E_MAIN_LLM ?? 'text-generation/Kimi-K2.6'
export const TASK_LLM = process.env.E2E_TASK_LLM ?? 'text-generation/gemma-4-31B-it'

export const KNOWLEDGE_COLLECTION = process.env.E2E_KNOWLEDGE_COLLECTION ?? ''
export const KNOWLEDGE_QUESTION = process.env.E2E_KNOWLEDGE_QUESTION ?? ''
export const KNOWLEDGE_ANSWER = process.env.E2E_KNOWLEDGE_ANSWER ?? ''

/** A knowledge database seeded with the table extraction corpus, see e2e/fixtures/knowledge-extraction/README.md. */
export const DOCUMENT_DATABASE = process.env.E2E_DOCUMENT_DATABASE ?? ''
export const DOCUMENT_COLLECTION = process.env.E2E_DOCUMENT_COLLECTION ?? ''
export const DOCUMENT_GLOB = process.env.E2E_DOCUMENT_GLOB ?? 'invoices/**'
export const DOCUMENT_SUPPLIER = process.env.E2E_DOCUMENT_SUPPLIER ?? 'ACME AG'
export const DOCUMENT_EXPECTED_ITEM = process.env.E2E_DOCUMENT_EXPECTED_ITEM ?? 'PSU-750'
/** A supplier with more invoices in the corpus than one answer extracts. */
export const DOCUMENT_BULK_SUPPLIER = process.env.E2E_DOCUMENT_BULK_SUPPLIER ?? 'Hooli AG'
/** The collection of the same database holding the supplier contracts and SLAs. */
export const DOCUMENT_LEGAL_COLLECTION = process.env.E2E_DOCUMENT_LEGAL_COLLECTION ?? 'legal'

export const LLM_TURN_TIMEOUT = 5 * 60_000
export const LLM_TEST_TIMEOUT = 15 * 60_000
