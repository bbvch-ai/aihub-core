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

## Decision

**Iterative, Python-based LLM whitepaper generator** with these key components:

1. **Iterative Chapter Generation**: Generate chapters sequentially, passing previous chapters as context to maintain
   narrative flow. Each prompt includes: glossary, previous chapters, source docs, chapter instructions.

2. **Python + Jinja2**: Use Python (not shell) with Jinja2 templates for clean separation of logic and content. More
   maintainable and testable than shell scripts.

3. **Centralized Glossary**: Single `glossary.md` defines all business terms (Agenten-Profil, Wissensdatenbank, etc.),
   included in every generation to ensure consistency.

4. **Manual CLI Triggering**: Generate via `./generate-whitepaper.py [chapters]` - deliberate regeneration, not
   automatic.

5. **LaTeX/PDF Output**: Direct markdown → LaTeX → PDF pipeline (no Word) for professional typesetting and full
   automation.

6. **Modular Architecture**: Separate files for glossary, general instructions, chapter prompts, source mappings, and
   templates - business stakeholders can edit requirements without touching code.

## Consequences

**Positive:**

- Ensures consistency in terminology and narrative flow across chapters
- Maintainable Python/Jinja2 code with clear separation of concerns
- Professional LaTeX output suitable for business presentations
- Flexible - prompts and glossary editable without code changes
- Cost-controlled through manual triggering

**Negative:**

- Requires Python environment and LaTeX knowledge
- Manual process - can become outdated if not regenerated
- Sequential generation takes 5-10 minutes for full whitepaper
- Requires LLM API access (no offline generation)
- Initial prompt engineering effort needed

**Key Trade-offs:**

- Manual vs. automatic: Chose manual for control over versioning
- Python vs. shell: Chose Python for maintainability over simplicity
- LaTeX vs. Word: Chose LaTeX for automation over familiarity
- Sequential vs. parallel: Chose sequential for consistency over speed
