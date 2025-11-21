# Whitepaper Iterative Refinement Workflow

This document describes the complete workflow for generating, measuring, and iteratively refining the Swiss AI-Hub
whitepaper until it meets quality and length targets.

## 🎯 Quality Targets

- **Length**: Maximum 40 Word pages (~12,000 words @ 300 words/page)
- **Quality**: Natural Fließtext (not AI-sounding), minimal bulletpoints, business-focused
- **Business Questions**: All 6 Kern-Dimensionen explicitly addressed
- **Datenschutz**: Given 30-50% more detail than other dimensions (Swiss priority)
- **Structure**: Each chapter standalone-readable with Konzept/Prozess/Technik sections

## 📊 Current Word Distribution

All chapter prompts have been updated with new word count targets:

| Chapter | Title                       | Target Words | Type      |
| ------- | --------------------------- | ------------ | --------- |
| 00      | Executive Summary           | 600-900      | kurz      |
| 01      | Business Challenge          | 400-600      | sehr kurz |
| 02      | Platform Overview           | 400-600      | sehr kurz |
| 03      | Benutzererfahrung           | 900-1300     | mittel    |
| 04      | Wissensmanagement & RAG     | 1300-1800    | lang      |
| 05      | AI-Agents                   | 1300-1800    | lang      |
| 06      | Prozessautomatisierung      | 600-900      | kurz      |
| 07      | Administration & Governance | 1300-1800    | lang      |
| 08      | Sicherheit                  | 1300-1800    | lang      |
| 09      | Compliance & Datenschutz    | 1800-2100    | sehr lang |
| 10      | Deployment & Betrieb        | 900-1300     | mittel    |

**Total Range**: 10,800-14,900 words (target midpoint: ~12,850)

## 🔄 Iterative Workflow

### Iteration Cycle

```
┌─────────────────────────────────────────────────────────┐
│  1. GENERATE → 2. COMBINE → 3. MEASURE → 4. ANALYZE    │
│                                ↓                         │
│                    ┌───────────┘                         │
│                    │                                     │
│  ← 5. REFINE PROMPTS (if not meeting targets)           │
└─────────────────────────────────────────────────────────┘
```

### Step-by-Step Instructions

#### 1. Generate Chapters

Generate all whitepaper chapters using the LLM:

```bash
cd /home/user/aihub-core/aihub_doc/whitepaper

# Generate all chapters (uses general_prompt.md + chapter-specific prompts)
./generate-whitepaper.sh

# Or generate specific chapters only:
./generate-whitepaper.sh 00 04 09
```

**What happens**:

- Script reads `general_prompt.md` (common guidelines for ALL chapters)
- Script reads `prompts/XX_prompt.md` (chapter-specific focus)
- Script reads source docs from `sources/XX_sources.txt`
- Combines into single prompt and calls LLM (default: gemini-2.5-flash)
- Outputs to `output/XX_output.md`

**Tips**:

- First run: Generate all chapters
- Subsequent iterations: Regenerate only chapters that need improvement
- Use better model for quality: `LLM_MODEL=claude-3-7-sonnet-20250219 ./generate-whitepaper.sh`

#### 2. Combine Chapters

Combine all generated chapters into a single document:

```bash
# Combine with table of contents (default)
./combine-whitepaper.sh

# Output: swiss_ai_hub_whitepaper.md and .docx
```

**What happens**:

- Reads all `output/XX_output.md` files
- Sorts by chapter number
- Adds table of contents
- Inserts page breaks between chapters (`\newpage`)
- Creates combined Markdown file
- Converts to Word document (if pypandoc/pandoc available)

#### 3. Measure Quality & Length

Measure the combined whitepaper against targets:

```bash
# Measure the combined document
./measure-whitepaper.sh swiss_ai_hub_whitepaper.md
```

**What it measures**:

**Length Metrics**:

- Total word count vs 12,000-word target
- Estimated pages @ 300 words/page
- Per-chapter word counts (identifies overly long chapters)

**Quality Metrics**:

- Bulletpoint ratio (should be low)
- "Die Plattform" repetition (phrase variation check)
- Filler phrase detection (AI-sounding text indicators)

**Business Coverage**:

- Checks for mentions of all 6 Kern-Dimensionen:
  - KOSTEN (Costs, TCO)
  - SICHERHEIT (Security)
  - DATENSCHUTZ (Privacy, revDSG, DSGVO)
  - MANAGEMENT (Operational complexity, administration)
  - ZUKUNFTSSICHERHEIT (Future-proofing, vendor lock-in)
  - INTEGRATION (Deployment, interoperability)

**Output**:

- Status: WITHIN TARGET or EXCEEDS TARGET
- Recommendations for improvement
- Word document with accurate page count

#### 4. Analyze Results

Review the measurement output and identify issues:

**If Total > 12,000 words**:

- Check per-chapter breakdown - which chapters are over their target?
- Are some chapters far longer than expected?
- Is Datenschutz chapter (09) appropriately longer (1800-2100 words)?

**If Quality Issues**:

- Too many bulletpoints? (> 50 per 1000 words)
- Repetitive phrasing? (e.g., "Die Plattform" > 15 per 1000 words)
- Filler phrases detected? (AI-like writing)
- Missing business dimensions?

**If Structure Issues**:

- Open individual chapter files in `output/XX_output.md`
- Check for standalone readability (no cross-references?)
- Check for Konzept/Prozess/Technik subsections (where appropriate)
- Check if Datenschutz questions are answered thoroughly

#### 5. Refine Prompts (if needed)

Based on analysis, refine prompts and regenerate:

**If a specific chapter is too long**:

1. Edit `prompts/XX_prompt.md`:

   - Reduce word count target further
   - Remove non-essential topics
   - Simplify structure

2. Regenerate that chapter:

   ```bash
   ./generate-whitepaper.sh XX
   ```

**If quality issues (bulletpoints, filler phrases)**:

1. Edit `general_prompt.md`:

   - Strengthen "Textfluss" guidelines
   - Add more examples of bad vs good writing
   - Increase emphasis on natural language

2. Regenerate affected chapters:

   ```bash
   ./generate-whitepaper.sh  # all chapters
   ```

**If business questions not answered**:

1. Check if `general_prompt.md` has the business questions section
2. Check if chapter prompt has `Business-Dimensionen` section
3. Strengthen emphasis in chapter prompt on specific dimensions
4. Regenerate:
   ```bash
   ./generate-whitepaper.sh XX
   ```

**If Datenschutz underemphasized**:

1. Edit `prompts/09_prompt.md` to strengthen Datenschutz focus
2. Check other chapters (04, 05, 07, 08) also cover Datenschutz aspects
3. Regenerate affected chapters

**After refinement**: Return to Step 1 (Generate) and repeat cycle.

## 🎯 Convergence Criteria

**Stop iterating when ALL of these are met**:

✅ Total word count: 10,800-13,000 words (within 10% of 12,000 target) ✅ No chapter exceeds its word count target by more
than 10% ✅ Bulletpoint ratio < 30 per 1000 words ✅ "Die Plattform" repetition < 10 per 1000 words ✅ No filler phrases
detected ✅ All 6 business dimensions mentioned (especially Datenschutz prominent) ✅ Each chapter reads naturally
(Fließtext, not AI-like) ✅ Word document page count: 35-42 pages

## 🛠️ Tool Reference

### generate-whitepaper.sh

**Usage**:

```bash
./generate-whitepaper.sh [chapter_ids...]

# Examples:
./generate-whitepaper.sh           # Generate all chapters
./generate-whitepaper.sh 00 04 09  # Generate specific chapters
./generate-whitepaper.sh --list    # List available chapters
```

**Environment Variables**:

```bash
LLM_MODEL=gpt-4 ./generate-whitepaper.sh        # Use different model
LLM_MODEL=claude-3-7-sonnet-20250219 ./generate-whitepaper.sh  # Claude
```

**Models Recommended**:

- **gemini-2.5-flash** (default): Fast, cost-effective, good quality
- **claude-3-7-sonnet-20250219**: Highest quality, best for business writing
- **gpt-4o**: Good balance of speed and quality

### combine-whitepaper.sh

**Usage**:

```bash
./combine-whitepaper.sh [output_dir] [output_name] [include_toc]

# Examples:
./combine-whitepaper.sh                        # Use defaults
./combine-whitepaper.sh ./output my_wp true    # Custom name with TOC
./combine-whitepaper.sh ./output wp false      # Without TOC
```

**Output**:

- `<output_name>.md` - Combined Markdown
- `<output_name>.docx` - Word document (if pypandoc available)

### measure-whitepaper.sh

**Usage**:

```bash
./measure-whitepaper.sh [combined_markdown]

# Examples:
./measure-whitepaper.sh                        # Use default swiss_ai_hub_whitepaper.md
./measure-whitepaper.sh custom_whitepaper.md   # Measure custom file
```

**Output**:

- Console report with:
  - Total words and estimated pages
  - Status (WITHIN TARGET / EXCEEDS TARGET)
  - Per-chapter breakdown
  - Quality indicators
  - Business dimension coverage
  - Recommendations
- Word document (if pandoc available) for accurate page count

## 📁 File Structure Reference

```
whitepaper/
├── generate-whitepaper.sh       # Main generation script
├── combine-whitepaper.sh        # Combination wrapper
├── combine_whitepaper.py        # Python combiner
├── measure-whitepaper.sh        # Quality & length measurement
├── general_prompt.md            # Common guidelines for ALL chapters
│                                # (Textfluss, Business-Fragen, Structure)
├── prompts/                     # Chapter-specific prompts
│   ├── 00_prompt.md            # What content to cover for each chapter
│   ├── 01_prompt.md            # Which business dimensions to focus on
│   └── ...
├── sources/                     # Source documentation lists
│   ├── 00_sources.txt          # Paths to docs for each chapter
│   ├── 01_sources.txt
│   └── ...
├── output/                      # Generated chapters
│   ├── 00_output.md
│   ├── 01_output.md
│   └── ...
├── swiss_ai_hub_whitepaper.md   # Combined final document (Markdown)
└── swiss_ai_hub_whitepaper.docx # Combined final document (Word)
```

## 💡 Tips for Quality

### For Natural Writing (Not AI-like)

❌ **Avoid**:

- Excessive bulletpoints (max 1-2 per subsection)
- Inflated language ("revolutionäre Plattform", "hochinnovative Lösung")
- Filler phrases ("Es ist wichtig zu betonen", "Darüber hinaus")
- Repetitive sentence starters
- Overly structured lists

✅ **Instead**:

- Write in flowing paragraphs with transition sentences
- Use concrete, specific language
- Vary sentence structure and length
- Connect ideas naturally
- Focus on answering reader's questions directly

### For Business Focus

✅ **Always Answer**:

- "What problem does this solve for my business?"
- "How much does it cost?" (TCO, not just licensing)
- "Is my data safe?" (Swiss context: revDSG, data residency)
- "Who manages it and how complex is it?"
- "What if I want to switch later?" (lock-in risks)
- "How does it integrate with what we have?"

### For Datenschutz Emphasis (Swiss Context)

The user explicitly requested that **Datenschutz** (data privacy) be given significantly more attention:

✅ **Chapter 09** (Compliance) should be longest (1800-2100 words) ✅ **Throughout all chapters**: Datenschutz aspects get
30-50% more detail ✅ **Specific questions to answer**:

- Where is data stored physically? (Switzerland, EU, USA?)
- Who has access? (Admin, Support, Cloud Provider?)
- How is data prevented from leaving Switzerland?
- Which laws are met? (revDSG, DSGVO, FADP)
- What happens if a user requests data deletion?
- How is data encrypted at rest and in transit?
- Can we audit all data processing?

### For Standalone Chapters

Each chapter must be readable independently:

✅ **No cross-references**: Don't say "as mentioned in Chapter X" ✅ **Self-contained intro**: 1 paragraph context (max
150 words) ✅ **Clear subsections**: Use Konzept/Prozess/Technik structure ✅ **Signaling for selective reading**: Readers
can skip technical sections if needed

## 🔧 Troubleshooting

### "llm command not found"

```bash
pipx install llm
llm keys set anthropic  # or openai, gemini
```

### "pypandoc not installed" (DOCX conversion)

```bash
pip install pypandoc
sudo apt install pandoc  # or: brew install pandoc
```

### Chapter generation fails

- Check API rate limits for your LLM provider
- Try with slower model: `LLM_MODEL=gemini-2.5-flash`
- Check source files exist: `cat sources/XX_sources.txt`
- Increase MAX_RETRIES in `generate-whitepaper.sh`

### Word document page count different from estimate

- Estimate uses 300 words/page (conservative)
- Actual Word page count depends on formatting, images, etc.
- Use actual Word document page count for final verification

### Chapter too long despite reduced target

- Remove entire subsections from chapter prompt
- Move content to other chapters
- Focus only on most critical business questions
- Check if bulletpoints are inflating length (convert to prose)

### Quality issues persist after prompt refinement

- Try different LLM model (Claude Sonnet better for natural writing)
- Add specific negative examples to `general_prompt.md`
- Manually edit problematic passages in `output/XX_output.md`
- Strengthen KRITISCH section in `general_prompt.md`

## 📚 Additional Documentation

- **README.md**: Project overview and system architecture
- **USAGE.md**: Quick start guide and command reference
- **general_prompt.md**: Detailed writing guidelines for LLM
- **prompts/XX_prompt.md**: Chapter-specific content guidelines

## 🎓 Best Practices

1. **Start with all chapters**: Generate complete whitepaper first to understand baseline
2. **Measure before refining**: Data-driven decisions based on measurement output
3. **Iterate on worst offenders first**: Fix longest chapters or lowest quality first
4. **Batch regenerate when changing general_prompt.md**: Changes affect all chapters
5. **Selective regenerate when changing chapter prompts**: Only affects that chapter
6. **Test with different models**: Claude Sonnet for quality, Gemini Flash for speed
7. **Commit after each successful iteration**: Git commit prompts and outputs together
8. **Manual polish at the end**: Final 5-10% can be manual editing of `output/*.md`

## 📈 Expected Timeline

**Initial Generation**: 30-60 minutes (all 11 chapters with Gemini Flash) **First Measurement**: 2 minutes **Analysis**:
10-20 minutes (review output, identify issues) **Prompt Refinement**: 15-30 minutes **Regeneration**: 15-45 minutes
(only affected chapters)

**Typical Iteration Count**: 2-4 iterations to meet all targets **Total Time**: 2-4 hours for complete high-quality
whitepaper

## ✅ Success Checklist

Before considering the whitepaper done:

- [ ] All chapters generated without errors
- [ ] Combined whitepaper created successfully
- [ ] Measurement shows WITHIN TARGET status
- [ ] Total word count: 10,800-13,000 words
- [ ] Word document: 35-42 pages
- [ ] All chapters under their individual word targets
- [ ] Bulletpoint ratio < 30 per 1000 words
- [ ] No excessive phrase repetition
- [ ] All 6 business dimensions covered
- [ ] Datenschutz given prominence (especially Chapter 09)
- [ ] Natural writing style (not AI-sounding)
- [ ] Each chapter standalone-readable
- [ ] No cross-references between chapters
- [ ] Konzept/Prozess/Technik sections where appropriate
- [ ] Manual review of at least 3 sample chapters
- [ ] Word document formatted correctly with page breaks

---

**Ready to start?**

```bash
cd /home/user/aihub-core/aihub_doc/whitepaper

# 1. Generate
./generate-whitepaper.sh

# 2. Combine
./combine-whitepaper.sh

# 3. Measure
./measure-whitepaper.sh swiss_ai_hub_whitepaper.md

# 4. Analyze output and refine prompts as needed

# 5. Repeat until targets met
```
