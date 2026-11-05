import { readFileSync, writeFileSync } from 'node:fs'
import path from 'node:path'

const FIXTURES = path.join(__dirname, '..', 'fixtures')

interface GroundTruth {
  'sales.xlsx': {
    q3_revenue_by_region: Record<'North' | 'South' | 'East' | 'West', number>
    lookup: { region: string; quarter: string; product: string; revenue: number }
  }
  'alpha.pdf': { code_name: string; lead: string }
  'bravo.pdf': { code_name: string; lead: string }
}

export const GROUND_TRUTH = JSON.parse(readFileSync(path.join(FIXTURES, 'ground_truth.json'), 'utf8')) as GroundTruth

export const SALES_XLSX = path.join(FIXTURES, 'sales.xlsx')
export const ALPHA_PDF = path.join(FIXTURES, 'alpha.pdf')
export const BRAVO_PDF = path.join(FIXTURES, 'bravo.pdf')
export const BROKEN_PDF = path.join(FIXTURES, 'broken.pdf')

export const LONG_REPORT_NAME = 'long-report.md'
export const LONG_REPORT_CODE_NAME = 'SAFFRON-LYNX-88'

/**
 * A report far beyond the 4,000-token tool-result limit, written per run instead of committed: ~35 KB of
 * near-identical sections would only bloat the repository. The planted fact sits in the last section.
 */
export function writeLongReport(directory: string): string {
  const sections = Array.from(
    { length: 120 },
    (_, index) =>
      `## Section ${index + 1}\n\nThe facilities team reviewed site ${index + 1} in week ${(index % 52) + 1}. ` +
      `Heating, lighting and access control were inspected and logged without findings. ` +
      `The next inspection of site ${index + 1} is planned for the following quarter.\n`,
  )
  const report = [
    '# Facilities inspection report',
    ...sections,
    `## Closing note\n\nThe code name of the facilities programme is ${LONG_REPORT_CODE_NAME}.\n`,
  ].join('\n')
  const file = path.join(directory, LONG_REPORT_NAME)
  writeFileSync(file, report)
  return file
}
