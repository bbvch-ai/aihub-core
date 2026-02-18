# Swiss AI-Hub Whitepaper Generator

Automated LLM-based system for generating business-focused whitepaper chapters from technical documentation.

## Directory Structure

```
whitepaper/
├── chapters/                          # Self-contained chapter folders
│   ├── 00-executive-summary/
│   │   ├── prompt.md                  # Chapter writing instructions
│   │   ├── sources.md                # Source doc mappings
│   │   └── output.md                  # Generated chapter
│   ├── 01-business-challenge/
│   │   └── ...
│   └── XX-chapter-name/
│       └── ...
├── config/                            # Configuration files
│   ├── glossary.md                    # Terminology definitions
│   ├── general_prompt.md              # General writing instructions
│   └── metadata.yaml                  # PDF metadata (title, author, date)
├── scripts/                           # Generation scripts
│   ├── generate-sources.py            # LLM-based source discovery
│   ├── generate-whitepaper.py         # Chapter generation
│   └── llm_utils.py                   # Shared utilities
├── templates/                         # Jinja2 prompt templates
│   └── full_prompt.j2
├── graphics/                          # Images for the whitepaper
├── build/                             # Build output
│   ├── whitepaper.tex                 # LaTeX template
│   └── whitepaper.pdf                 # Generated PDF
├── Makefile                           # Build automation
└── README.md
```

## How It Works

The generator consists of two scripts:

1. **`generate-sources.py`** - LLM-based source discovery (optional, run when docs change)
2. **`generate-whitepaper.py`** - Chapter generation from sources

### Source Discovery

The source discovery script scans all documentation files and uses an LLM to determine which docs are relevant for each
chapter. This eliminates manual maintenance of `sources.md` files as documentation grows.

### Chapter Generation

The generator builds a combined prompt containing:

1. **Terminology Glossary** (`config/glossary.md`) - Consistent term definitions
2. **Previous Chapters** (from earlier `chapters/*/output.md`) - For style consistency
3. **Source Documentation** (from `chapters/XX/sources.md`) - Technical facts
4. **Chapter Instructions** (`chapters/XX/prompt.md`) - What to write
5. **General Guidelines** (`config/general_prompt.md`) - Writing style

This prompt is sent to an LLM, which generates a polished business chapter.

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
python scripts/generate-sources.py

# 2. Generate whitepaper chapters
python scripts/generate-whitepaper.py

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
python scripts/generate-sources.py

# Update specific chapters only
python scripts/generate-sources.py 03-data-sovereignty 05-administration-governance

# Preview without writing files
python scripts/generate-sources.py --dry-run

# List chapters and their source counts
python scripts/generate-sources.py --list

# Use a different model
python scripts/generate-sources.py --model claude-3-5-sonnet-20241022
```

The script:

1. Scans all `*.en.md` files in `aihub_doc/docs/`
2. Extracts title and summary from each file
3. Sends chapter prompt + doc manifest to LLM
4. LLM returns relevant file paths
5. Writes validated paths to `chapters/XX/sources.md`

**Note:** Generated source files can be manually adjusted. The script adds a comment indicating they were
auto-generated.

### Chapter Generation (generate-whitepaper.py)

Generate All Chapters

```bash
python scripts/generate-whitepaper.py
```

### Generate Specific Chapters

```bash
python scripts/generate-whitepaper.py 00 03
```

### List Available Chapters

```bash
python scripts/generate-whitepaper.py --list
```

### Use Different Model

```bash
python scripts/generate-whitepaper.py --model claude-3-5-sonnet-20241022
python scripts/generate-whitepaper.py --model gpt-4
```

### Get Help

```bash
python scripts/generate-whitepaper.py --help
```

## Key Features

### 1. Chapter-Centric Organization

Each chapter is self-contained in its own folder with all related files:

- `prompt.md` - Writing instructions for this chapter
- `sources.md` - Documentation files to use as source material
- `output.md` - Generated chapter content

This makes it easy to understand what each chapter is about and find all related files.

### 2. Terminology Glossary

The `config/glossary.md` file ensures consistent terminology across all chapters. When you define terms here, the LLM
will use them consistently throughout the whitepaper.

### 3. Intelligent Regeneration

When regenerating an existing chapter, the script:

- Includes the current version in the prompt
- Instructs the LLM to improve it with new information
- Preserves manual edits that don't conflict with source docs
- Maintains consistent style

### 4. Chapter Consistency

The script automatically includes all previously generated chapters in the prompt to ensure:

- Consistent writing style
- Coherent narrative flow
- No repetition across chapters

### 5. Automatic Formatting

Generated markdown files are automatically formatted using `mdformat` with your project's `pyproject.toml` configuration
(line wrapping at 120 characters, GFM extensions, etc.).

### 6. Cost Tracking

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

## Creating a New Chapter

### 1. Create Chapter Directory

```bash
mkdir chapters/XX-chapter-name
```

### 2. Create Chapter Prompt: `chapters/XX-chapter-name/prompt.md`

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

### 3. Discover Sources Automatically

```bash
# Let LLM find relevant documentation
python scripts/generate-sources.py XX-chapter-name

# Review the generated sources file
cat chapters/XX-chapter-name/sources.md
```

Alternatively, create `chapters/XX-chapter-name/sources.md` manually:

```
# Source Documentation for Chapter X
# Paths relative to aihub_doc/docs/

2_platform/8_knowledges/index.en.md
2_platform/5_agents/2_rag_agent/index.en.md
```

### 4. Generate the Chapter

```bash
python scripts/generate-whitepaper.py XX-chapter-name
```

### 5. Review and Iterate

- Review `chapters/XX-chapter-name/output.md`
- Refine prompt if needed
- Regenerate until satisfied

## Glossary Management

The `config/glossary.md` file defines standard terminology. When adding terms:

1. **Verwendung:** How to write it (e.g., "Agenten-Profil")
2. **Definition:** What it means
3. **Kontext:** Additional context or usage notes

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
- Check `chapters/XX/sources.md` for typos

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

Then update `scripts/generate-whitepaper.py` to pass the new variables to `template.render()`.

## Support

- **LLM CLI**: https://github.com/simonw/llm
- **Jinja2 Docs**: https://jinja.palletsprojects.com/
- **Project Repo**: https://github.com/bbvch-ai/aihub-core
