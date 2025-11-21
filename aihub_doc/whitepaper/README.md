# Swiss AI-Hub Whitepaper Generator

Automated LLM-based whitepaper generation system for creating business-focused documentation from technical docs.

## Table of Contents

- [Overview](#overview)
  - [How Prompts Are Combined](#how-prompts-are-combined)
- [Directory Structure](#directory-structure)
- [Prerequisites](#prerequisites)
- [Usage](#usage)
  - [Generate All Chapters](#generate-all-chapters)
  - [Generate Specific Chapters](#generate-specific-chapters)
  - [List Available Chapters](#list-available-chapters)
  - [Use Different Model](#use-different-model)
  - [Help](#help)
- [Creating a New Chapter](#creating-a-new-chapter)
- [Prompt Writing Guidelines](#prompt-writing-guidelines)
  - [Structure Your Prompts With](#structure-your-prompts-with)
  - [Best Practices](#best-practices)
- [Source File Guidelines](#source-file-guidelines)
  - [Format](#format)
  - [Selection Criteria](#selection-criteria)
  - [Finding Source Docs](#finding-source-docs)
- [Tips for Quality Output](#tips-for-quality-output)
- [Chapter Numbering Convention](#chapter-numbering-convention)
- [Troubleshooting](#troubleshooting)
  - [Error: "llm command not found"](#error-llm-command-not-found)
  - [Error: "API key not set"](#error-api-key-not-set)
  - [Output is too technical](#output-is-too-technical)
  - [Output doesn't cover all requirements](#output-doesnt-cover-all-requirements)
  - [Generation fails](#generation-fails)
- [Advanced Usage](#advanced-usage)
  - [Custom System Prompt for All Chapters](#custom-system-prompt-for-all-chapters)
  - [Parallel Generation](#parallel-generation)
  - [Post-Processing](#post-processing)
- [Best Practices for Production](#best-practices-for-production)
- [Example Workflow](#example-workflow)
- [Support](#support)

---

## Overview

This system generates whitepaper chapters by building a single combined prompt that contains:

1. **Chapter Instructions** - From `prompts/NN_prompt.md` (what to write, how to write it)
2. **Source Documentation** - From technical docs listed in `sources/NN_sources.txt` (factual content)
3. **Task Instruction** - Clear directive to generate the chapter

This combined prompt is sent to an LLM which outputs a polished business-focused chapter.

### How Prompts Are Combined

The script builds a single text prompt like this:

```
# WHITEPAPER CHAPTER GENERATION

You are writing a whitepaper chapter for the Swiss AI-Hub platform.
Below you will find:
1. Chapter instructions and requirements
2. Source documentation from technical docs

═══════════════════════════════════════════════════════════════

## CHAPTER INSTRUCTIONS

[Content from prompts/07_prompt.md]
# Chapter 7: Administration and Governance
## Chapter Objective
Describe the administrative and governance capabilities...
[... full prompt file ...]

═══════════════════════════════════════════════════════════════

## SOURCE DOCUMENTATION

Below is the technical documentation you should use as source material:

### Source File: 2_platform/11_access_management/1_authentication_setup/index.en.md

[Full content of authentication_setup doc]

---

### Source File: 2_platform/11_access_management/2_permissions/index.en.md

[Full content of permissions doc]

---

### Source File: 2_platform/14_cost_control/index.en.md

[Full content of cost_control doc]

---

[... all source files concatenated ...]

═══════════════════════════════════════════════════════════════

## YOUR TASK

Now generate the chapter content according to the instructions above,
using the source documentation as your factual basis.
```

Then this entire combined prompt is piped to the LLM:

```bash
echo "$combined_prompt" | llm --no-stream -m claude-3-7-sonnet-20250219
```

Simple and readable!

## Directory Structure

```
whitepaper/
├── generate-whitepaper.sh    # Main generation script
├── prompts/                   # Chapter prompts with instructions
│   ├── 00_prompt.md          # Executive Summary prompt
│   ├── 03_prompt.md          # User Experience prompt
│   ├── 07_prompt.md          # Administration prompt
│   └── NN_prompt.md          # Additional chapters...
├── sources/                   # Source documentation mappings
│   ├── 00_sources.txt        # Docs to use for Executive Summary
│   ├── 03_sources.txt        # Docs to use for User Experience
│   ├── 07_sources.txt        # Docs to use for Administration
│   └── NN_sources.txt        # Additional chapter sources...
├── output/                    # Generated chapter outputs
│   ├── 00_output.md          # Generated Executive Summary
│   ├── 03_output.md          # Generated User Experience chapter
│   ├── 07_output.md          # Generated Administration chapter
│   └── NN_output.md          # Additional generated chapters...
└── README.md                  # This file
```

## Prerequisites

1. **Install LLM CLI tool**:

   ```bash
   pipx install llm
   ```

   See: https://github.com/simonw/llm

2. **Configure API keys** (for your chosen model):

   ```bash
   # For Claude:
   llm keys set anthropic

   # For OpenAI:
   llm keys set openai

   # For Gemini:
   llm keys set gemini
   ```

3. **Set model** (optional - default is gemini-2.5-flash):

   ```bash
   # Default model (already set in script):
   # LLM_MODEL=gemini-2.5-flash

   # Override with different model:
   export LLM_MODEL=claude-3-7-sonnet-20250219
   # or
   export LLM_MODEL=gpt-4-turbo
   ```

## Usage

### Generate All Chapters

```bash
./generate-whitepaper.sh
```

### Generate Specific Chapters

```bash
./generate-whitepaper.sh 00 03 07
```

### List Available Chapters

```bash
./generate-whitepaper.sh --list
```

### Use Different Model

```bash
LLM_MODEL=gpt-4 ./generate-whitepaper.sh 00
```

### Help

```bash
./generate-whitepaper.sh --help
```

## Creating a New Chapter

To add a new chapter (e.g., Chapter 04: Knowledge Management):

### 1. Create Prompt File: `prompts/04_prompt.md`

```markdown
# Chapter 4: Knowledge Management and RAG

## Chapter Objective
Describe how Swiss AI-Hub manages organizational knowledge...

## Target Audience
- Decision makers evaluating knowledge capabilities
- Administrators planning knowledge organization

## Key Topics to Cover
- Knowledge organization (databases, collections, documents)
- Content ingestion (manual upload, auto-sync)
- Document processing (parsing, OCR, chunking)
- RAG-based retrieval

## RFP Requirements Addressed
- Admin: RAG mit spezifischen Kontexten ✓
- Admin: Mehrere parallele Datenquellen ✓
- Admin: Crawling öffentlicher Inhalte ✓
...

## Questions This Chapter Must Answer
- How is organizational knowledge structured?
- How does content get into the system?
- How are documents processed?
...

## Writing Style
- Tone: Practical, knowledge-management focused
- Length: 5-6 pages (2000-2400 words)
...
```

### 2. Create Sources File: `sources/04_sources.txt`

```
# Source Documentation for Chapter 4
# Paths relative to aihub_doc/docs/

2_platform/8_knowledges/index.en.md
2_platform/8_knowledges/1_namespaces/index.en.md
2_platform/6_pipelines/2_rag_ingestion_pipeline/index.en.md
2_platform/5_agents/2_rag_agent/index.en.md
```

### 3. Generate the Chapter

```bash
./generate-whitepaper.sh 04
```

### 4. Review and Edit Output

The generated chapter will be in `output/04_output.md`. Review for:

- Accuracy (verify against source docs)
- Completeness (all key topics covered)
- Business language (accessible to non-technical readers)
- RFP requirement coverage (explicitly mentioned where relevant)

## Prompt Writing Guidelines

### Structure Your Prompts With:

1. **Chapter Objective**: What this chapter accomplishes
2. **Target Audience**: Who will read this
3. **Key Topics to Cover**: Main sections (numbered as 7.1, 7.2, etc.)
4. **RFP Requirements Addressed**: Which requirements this chapter covers
5. **Questions to Answer**: What readers will learn
6. **Writing Style**: Tone, language, format, length
7. **Structure**: How to organize the content
8. **Important Guidelines**: Special instructions and emphasis areas
9. **Business Value to Emphasize**: Key takeaways for decision makers

### Best Practices:

- **Be specific**: Don't just say "describe RBAC", say "explain how kundenseitiger Admin role enables customer-side
  administration"
- **Reference requirements**: Link to specific RFP requirements naturally
- **Specify length**: Give word count targets (e.g., "6-8 pages, 2400-3200 words")
- **Set tone**: Be explicit about business vs. technical language
- **Provide examples**: "Show concrete examples like..."
- **Emphasize value**: Always include "Business Value to Emphasize" section

## Source File Guidelines

### Format:

```
# Source Documentation for Chapter X: Title
# List paths relative to aihub_doc/docs/

# Main sources
path/to/first/doc.md
path/to/second/doc.md

# Supporting sources
path/to/supporting/doc.md
```

### Selection Criteria:

1. **Relevance**: Only include docs directly relevant to chapter topic
2. **Completeness**: Include all docs needed to answer chapter questions
3. **Order**: List most important sources first
4. **Comments**: Use `#` for organizational comments

### Finding Source Docs:

```bash
# Search for topics
find ../docs -name "*.en.md" | xargs grep -l "RBAC"

# List by section
ls ../docs/2_platform/*/index.en.md

# View doc structure
tree ../docs -L 3
```

## Tips for Quality Output

### 1. Iterate on Prompts

Start with a simple prompt, generate, review, refine the prompt, regenerate.

### 2. Provide Context

The more specific your prompt, the better the output. Include:

- Exact terminology to use
- Specific examples to reference
- Format requirements
- What to emphasize vs. what to minimize

### 3. Review Generated Content

Always review for:

- Accuracy (check against source docs)
- Completeness (all topics covered)
- Consistency (terminology matches other chapters)
- Business focus (not too technical)

### 4. Version Control

Commit both prompts and outputs. Track what prompt generated what output.

### 5. Test Different Models

Different models have different strengths:

- **Claude Sonnet**: Best for long-form, nuanced business writing
- **GPT-4 Turbo**: Fast, good for technical accuracy
- **Gemini Flash**: Very fast, good for drafts

## Chapter Numbering Convention

- `00` - Executive Summary
- `01` - Business Challenge
- `02` - Platform Overview
- `03` - User Experience
- `04` - Knowledge Management
- `05` - AI Agents
- `06` - Process Automation
- `07` - Administration and Governance
- `08` - Security Architecture
- `09` - Regulatory Compliance
- `10` - Deployment and Operations
- `11` - AI Model Management
- `12` - Integration and Interoperability
- `13` - Transparency and Traceability
- `14` - Reliability and Quality
- `15` - Extensibility
- `16` - ISO Certifications
- `17` - Use Cases
- `18` - Implementation Roadmap
- `19` - Conclusion

## Troubleshooting

### Error: "llm command not found"

```bash
pipx install llm
```

### Error: "API key not set"

```bash
llm keys set anthropic  # or openai, gemini
```

### Output is too technical

Revise prompt to emphasize:

- "Write in business language accessible to non-technical decision makers"
- "Avoid technical implementation details"
- "Focus on WHAT and WHY, not HOW"

### Output doesn't cover all requirements

Add explicit instruction:

- "This chapter must address the following RFP requirements: [list]"
- "Explain how each requirement is met with concrete examples"

### Generation fails

- Check source files exist and paths are correct
- Try with smaller model (gemini-flash) for testing
- Check API rate limits
- Increase MAX_RETRIES in script

## Advanced Usage

### Custom System Prompt for All Chapters

Edit `generate-whitepaper.sh` and modify the llm call to add a base system prompt:

```bash
llm --no-stream -m "$LLM_MODEL" --system "You are an expert technical writer creating business-focused documentation. $prompt_content" <<EOF
...
EOF
```

### Parallel Generation

Generate multiple chapters in parallel:

```bash
for chapter in 00 03 07; do
    ./generate-whitepaper.sh $chapter &
done
wait
```

### Post-Processing

Add custom post-processing to format output:

```bash
./generate-whitepaper.sh 00
pandoc output/00_output.md -o output/00_output.pdf
```

## Best Practices for Production

1. **Version Control**: Commit prompts, sources, and outputs
2. **Review Process**: Have technical and business reviewers
3. **Consistency Check**: Ensure terminology consistent across chapters
4. **Fact Check**: Verify all technical claims against source docs
5. **RFP Mapping**: Create a checklist of all requirements and which chapter covers each
6. **Iterative Refinement**: Generate → Review → Refine prompt → Regenerate

## Example Workflow

```bash
# 1. Create prompt and sources
vi prompts/04_prompt.md
vi sources/04_sources.txt

# 2. Generate chapter
./generate-whitepaper.sh 04

# 3. Review output
less output/04_output.md

# 4. If not satisfied, refine prompt
vi prompts/04_prompt.md

# 5. Regenerate
./generate-whitepaper.sh 04

# 6. Once satisfied, commit
git add prompts/04_prompt.md sources/04_sources.txt output/04_output.md
git commit -m "docs: Add Chapter 4 - Knowledge Management"
```

## Support

For issues with:

- **Script**: Check this README and script comments
- **LLM tool**: https://github.com/simonw/llm
- **Source docs**: Refer to main documentation in `../docs/`
- **Prompts**: See examples in `prompts/` directory
