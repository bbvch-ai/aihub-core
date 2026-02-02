# Swiss AI-Hub Whitepaper Generator

Automated LLM-based system for generating business-focused whitepaper chapters from technical documentation.

## How It Works

The generator consists of two scripts:

1. **`generate-sources.py`** - LLM-based source discovery (optional, run when docs change)
2. **`generate-whitepaper.py`** - Chapter generation from sources

### Source Discovery

The source discovery script scans all documentation files and uses an LLM to determine which docs are relevant for each
chapter. This eliminates manual maintenance of `sources/*.txt` files as documentation grows.

### Chapter Generation

The generator builds a combined prompt containing:

1. **Terminology Glossary** (`glossary.md`) - Consistent term definitions
2. **Previous Chapters** (`output/`) - For style consistency
3. **Source Documentation** (from `sources/XX_sources.txt`) - Technical facts
4. **Chapter Instructions** (`prompts/XX_prompt.md`) - What to write
5. **General Guidelines** (`general_prompt.md`) - Writing style

This prompt is sent to an LLM, which generates a polished business chapter. The generator uses **Jinja2 templates** for
clean, maintainable prompt construction.

## Directory Structure

```
whitepaper/
├── generate-sources.py        # LLM-based source discovery
├── generate-whitepaper.py     # Main chapter generator
├── glossary.md                # Terminology definitions
├── general_prompt.md          # General writing instructions
├── templates/                 # Jinja2 prompt templates
│   └── full_prompt.j2
├── prompts/                   # Chapter-specific prompts
│   ├── 00_prompt.md          # Executive Summary
│   ├── 01_prompt.md          # Business Challenge
│   └── XX_prompt.md          # More chapters...
├── sources/                   # Source doc mappings (auto-generated)
│   ├── 00_sources.txt        # Docs for Executive Summary
│   ├── 01_sources.txt        # Docs for Business Challenge
│   └── XX_sources.txt        # More sources...
├── output/                    # Generated chapters
│   ├── 00_output.md
│   ├── 01_output.md
│   └── XX_output.md
├── whitepaper.tex             # LaTeX template for PDF
├── metadata.yaml              # PDF metadata (title, author, date)
└── whitepaper.pdf             # Generated PDF output
```

## Prerequisites

```bash
# 1. Install LLM CLI tool
pipx install llm

# 2. Install Python dependencies
pip install jinja2

# 3. Install mdformat for automatic formatting (optional but recommended)
pip install mdformat mdformat-gfm mdformat-frontmatter mdformat-myst mdformat-pyproject

# 4. Configure API key for your LLM provider
llm keys set gemini      # For Gemini (default)
llm keys set anthropic   # For Claude
llm keys set openai      # For GPT-4

# 5. Install pandoc and LaTeX for PDF generation
# macOS:
brew install pandoc
brew install --cask mactex

# Ubuntu/Debian:
sudo apt install pandoc texlive-xetex texlive-fonts-recommended
```

## Usage

### Recommended Workflow (Makefile)

```bash
# Full pipeline: discover sources, generate chapters, build PDF
make all

# Or run individual steps:
make sources    # Update source mappings
make chapters   # Generate whitepaper chapters
make pdf        # Build PDF from chapters

# Clean generated files
make clean
```

### Manual Workflow

```bash
# 1. Update source mappings when documentation changes
./generate-sources.py

# 2. Generate whitepaper chapters
./generate-whitepaper.py

# 3. Build PDF
make pdf
```

### Source Discovery (generate-sources.py)

Automatically discovers which documentation files are relevant for each chapter using LLM analysis. Run this when:

- Documentation structure changes (new files, renamed files, deleted files)
- Chapter prompts are updated with new topics
- You want to refresh source mappings

```bash
# Update sources for all chapters
./generate-sources.py

# Update specific chapters only
./generate-sources.py 03 05 07

# Preview without writing files
./generate-sources.py --dry-run

# List chapters and their source counts
./generate-sources.py --list

# Use a different model
./generate-sources.py --model claude-3-5-sonnet-20241022
```

The script:

1. Scans all `*.en.md` files in `aihub_doc/docs/`
2. Extracts title and summary from each file
3. Sends chapter prompt + doc manifest to LLM
4. LLM returns relevant file paths
5. Writes validated paths to `sources/XX_sources.txt`

**Note:** Generated source files can be manually adjusted. The script adds a comment indicating they were auto-generated.

### Chapter Generation (generate-whitepaper.py)

Generate All Chapters

```bash
./generate-whitepaper.py
```

### Generate Specific Chapters

```bash
./generate-whitepaper.py 00 03 07
```

### List Available Chapters

```bash
./generate-whitepaper.py --list
```

### Use Different Model

```bash
./generate-whitepaper.py --model claude-3-5-sonnet-20241022
./generate-whitepaper.py --model gpt-4
```

### Get Help

```bash
./generate-whitepaper.py --help
```

## Key Features

### 1. Terminology Glossary

The `glossary.md` file ensures consistent terminology across all chapters. When you define terms here, the LLM will use
them consistently throughout the whitepaper.

### 2. Intelligent Regeneration

When regenerating an existing chapter, the script:

- Includes the current version in the prompt
- Instructs the LLM to improve it with new information
- Preserves manual edits that don't conflict with source docs
- Maintains consistent style

### 3. Chapter Consistency

The script automatically includes all previously generated chapters in the prompt to ensure:

- Consistent writing style
- Coherent narrative flow
- No repetition across chapters

### 4. Automatic Formatting

Generated markdown files are automatically formatted using `mdformat` with your project's `pyproject.toml` configuration
(line wrapping at 120 characters, GFM extensions, etc.).

### 5. Cost Tracking

Both scripts track token usage and display an estimated cost summary at the end of each run:

```
💰 Usage Summary
────────────────────────────────────
  LLM Calls:      17
  Input tokens:   245,000
  Output tokens:  42,000
  Total tokens:   287,000
  Est. cost:      $0.5940 USD
```

Pricing is based on official Gemini API rates from https://ai.google.dev/gemini-api/docs/pricing

## Creating a New Chapter

### 1. Create Chapter Prompt: `prompts/XX_prompt.md`

```markdown
# Chapter X: Your Title

## Chapter Objective
Describe what this chapter accomplishes...

## Target Audience
- Decision makers evaluating...
- Administrators planning...

## Key Topics to Cover
- Topic 1
- Topic 2
- Topic 3

## Questions This Chapter Must Answer
- Question 1?
- Question 2?

## Writing Style
- Tone: Business-focused, accessible
- Length: 5-6 pages (2000-2400 words)
```

### 2. Discover Sources Automatically

```bash
# Let LLM find relevant documentation
./generate-sources.py XX

# Review the generated sources file
cat sources/XX_sources.txt
```

Alternatively, create `sources/XX_sources.txt` manually:

```
# Source Documentation for Chapter X
# Paths relative to aihub_doc/docs/

2_platform/8_knowledges/index.en.md
2_platform/5_agents/2_rag_agent/index.en.md
```

### 3. Generate the Chapter

```bash
./generate-whitepaper.py XX
```

### 4. Review and Iterate

- Review `output/XX_output.md`
- Refine prompt if needed
- Regenerate until satisfied

## Glossary Management

The `glossary.md` file defines standard terminology. When adding terms:

1. **Verwendung:** How to write it (e.g., "Agenten-Profil")
3. **Definition:** What it means
4. **Kontext:** Additional context or usage notes

The glossary is automatically included in every chapter generation prompt.

## Model Selection

Different models have different strengths:

- **gemini-3-pro-preview** (default): Powerhorse, best quality
- **gemini-2.5-flash**: Fast, cost-effective, good quality
- **claude-3-5-sonnet**: Best for nuanced business writing
- **gpt-4**: Strong technical accuracy

## Troubleshooting

### "llm command not found"

```bash
pipx install llm
```

### "API key not set"

```bash
llm keys set gemini  # or anthropic, openai
```

### Output is too technical

Update the chapter prompt to emphasize:

- "Write in business language accessible to non-technical decision makers"
- "Focus on WHAT and WHY, not HOW"

### Output doesn't cover requirements

Add to the chapter prompt:

- "This chapter must address: [specific requirements]"
- "Provide concrete examples for each requirement"

### Generation fails

- Verify source file paths are correct
- Check API rate limits
- Try a different model
- Check `sources/XX_sources.txt` for typos

### No line breaks in output

Make sure mdformat plugins are installed:

```bash
pip install mdformat-pyproject mdformat-gfm mdformat-frontmatter mdformat-myst
```

## Best Practices

1. **Run source discovery first** when documentation changes significantly
2. **Generate sequentially** (00, 01, 02...) for best consistency
3. **Review and iterate** on prompts before moving to next chapter
4. **Commit everything** - prompts, sources, outputs, and glossary
5. **Update glossary first** when introducing new terminology
6. **Test with different models** to find the best fit for each chapter
7. **Review auto-generated sources** - LLM discovery is good but not perfect; adjust manually if needed
8. **Use dry-run mode** (`--dry-run`) to preview source discovery before committing

## Advanced: Template Customization

Edit `templates/full_prompt.j2` to customize the prompt structure:

```jinja2
## MY CUSTOM SECTION

{{ my_custom_variable }}

{% if condition %}
Conditional content here
{% endif %}

{% for item in items %}
- {{ item }}
{% endfor %}
```

Then update `generate-whitepaper.py` to pass the new variables to `template.render()`.

## Support

- **LLM CLI**: https://github.com/simonw/llm
- **Jinja2 Docs**: https://jinja.palletsprojects.com/
- **Project Repo**: https://github.com/bbvch-ai/aihub-core
