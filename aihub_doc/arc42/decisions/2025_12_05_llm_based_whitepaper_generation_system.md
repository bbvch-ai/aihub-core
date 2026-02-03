# LLM-Based Iterative Whitepaper Generation System

## Context

We need automated whitepaper generation that transforms technical documentation into business-focused content for
decision-makers. The whitepaper must stay synchronized with technical docs but be regenerated manually (not
automatically like technical docs). Traditional manual creation is time-consuming and becomes inconsistent.

## Decision Drivers

- **Consistency**: Terminology and narrative flow must be consistent across all chapters
- **Maintainability**: Shell scripts don't scale; need readable, maintainable code with templates
- **Professional Output**: LaTeX provides automated, professional typesetting without Word dependencies
- **Manual Control**: Whitepaper updates are deliberate, not automatic with every code change
- **Source Synchronization**: Source-to-chapter mappings must stay in sync as documentation grows
- **Discoverability**: Should be immediately clear what each chapter is about
- **Cohesion**: Related files (prompt, sources, output) should be grouped together

## Decision

**Iterative, Python-based LLM whitepaper generator** with chapter-centric organization:

### Directory Structure

```
whitepaper/
├── chapters/                          # Self-contained chapter folders
│   ├── 00-executive-summary/
│   │   ├── prompt.md                  # Writing instructions
│   │   ├── sources.txt                # Source doc mappings
│   │   └── output.md                  # Generated output
│   ├── 01-business-challenge/
│   └── ...
├── config/                            # Configuration
│   ├── glossary.md                    # Terminology definitions
│   ├── general_prompt.md              # Writing style guidelines
│   └── metadata.yaml                  # PDF metadata
├── scripts/                           # Generation scripts
│   ├── generate-whitepaper.py
│   ├── generate-sources.py
│   └── llm_utils.py
├── templates/                         # Jinja2 templates
├── graphics/                          # Images
├── build/                             # Build artifacts
│   ├── whitepaper.tex
│   └── whitepaper.pdf
└── Makefile
```

### Key Components

1. **Chapter-Centric Organization**: Each chapter is a self-contained folder with descriptive name
   (e.g., `03-data-sovereignty` instead of just `03`). All related files (prompt, sources, output) live together.

2. **LLM-Based Source Discovery**: `generate-sources.py` uses LLM to automatically discover which documentation files
   are relevant for each chapter. This eliminates manual maintenance as documentation evolves.

3. **Iterative Chapter Generation**: Generate chapters sequentially, passing previous chapters as context to maintain
   narrative flow. Each prompt includes: glossary, previous chapters, source docs, chapter instructions.

4. **Python + Jinja2**: Use Python (not shell) with Jinja2 templates for clean separation of logic and content.

5. **Centralized Glossary**: Single `config/glossary.md` defines all business terms, included in every generation.

6. **Manual CLI Triggering**: Generate via `make all` or individual scripts - deliberate regeneration, not automatic.

7. **LaTeX/PDF Output**: Direct markdown → LaTeX → PDF pipeline for professional typesetting.

8. **Separation of Concerns**: Scripts in `scripts/`, config in `config/`, build output in `build/`.

## Consequences

**Positive:**

- Ensures consistency in terminology and narrative flow across chapters
- Maintainable Python/Jinja2 code with clear separation of concerns
- Professional LaTeX output suitable for business presentations
- Flexible - prompts and glossary editable without code changes
- Cost-controlled through manual triggering
- Source mappings stay synchronized with documentation automatically via LLM discovery
- Chapter folders immediately show what each chapter covers
- All chapter-related files in one place (easier to review, modify, delete)
- Easy to add new chapters (create folder with 3 files)

**Negative:**

- Requires Python environment and LaTeX knowledge
- Manual process - can become outdated if not regenerated
- Sequential generation takes 5-10 minutes for full whitepaper
- Requires LLM API access (no offline generation)
- Initial prompt engineering effort needed
- LLM source discovery is non-deterministic (may vary slightly between runs)

**Key Trade-offs:**

- Manual vs. automatic: Chose manual for control over versioning
- Python vs. shell: Chose Python for maintainability over simplicity
- LaTeX vs. Word: Chose LaTeX for automation over familiarity
- Sequential vs. parallel: Chose sequential for consistency over speed
- Chapter folders vs. flat files: Chose folders for discoverability over simplicity
- LLM vs. embedding-based source discovery: Chose simple LLM-only approach for lower complexity
