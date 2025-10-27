---
title: Internationalization
index: 6
---

# Internationalization

The platform supports Switzerland's four national languages: German, English, French, and Italian. Users can work in their preferred language throughout the interface.

## Language support

German serves as the default language, but all four languages work identically. The interface, error messages, help text, and navigation all include translations.

All user-facing text has translations—form validation, dialogs, notifications, error messages, help documentation, and instructions. Users see no untranslated elements or mixed languages.

Dynamically generated content also respects language preferences. Service descriptions, agent names, and knowledge namespace labels adapt to the selected language.

Users select their language during authentication or in profile settings. The selection persists across sessions.

## Language selection and switching

Users configure their language in their profile. This becomes the default for all sessions across devices.

Users can temporarily switch languages for a specific session. This helps multilingual users who prefer different languages for different tasks.

Language changes apply immediately without reloading the page. All text updates instantly.

URLs don't include language codes. Shared links show content in the recipient's preferred language, not the sender's.

## Translation architecture

All user-facing text uses translation keys instead of hardcoded strings. Developers reference keys like `agent.create.title` rather than literal text. Translations can be modified without code changes.

Translations live in YAML files organized by service and language. Each service maintains its own translation files for all four languages.

Translation keys follow a hierarchical structure: `knowledge.namespace.create.label`. This prevents naming collisions and makes translations discoverable.

If a translation is missing in the selected language, the system falls back to German. If German is also missing, it displays the translation key itself.

## Terminology consistency

Shared glossaries define standard translations for common terms like "agent," "thread," "namespace," and "process." Services reference these shared translations instead of creating their own variants.

Domain-specific glossaries handle specialized terminology—technical AI concepts, Swiss regulatory terms, and industry-specific language.

Translations should undergo professional review by native speakers familiar with the technical concepts. This produces natural phrasing and appropriate terminology.

Translation updates deploy independently of code changes.

## Localized content handling

User-created resources can include translations for all supported languages. Administrators can provide a knowledge namespace name and description in German, English, French, and Italian.

The system can automatically detect document language for processing and knowledge management. This enables language-specific search optimization and retrieval.

Numbers, dates, times, and currencies format according to locale conventions. German users see dates as "31.12.2024," while English users see "12/31/2024."

Search functionality uses language-specific tokenization and stemming. German searches use German linguistic rules, French searches use French rules.

## Administrative considerations

Administrators can review and modify translations through dedicated interfaces. They can update terminology or add custom translations without editing YAML files.

Administrative dashboards show translation completeness across languages, identifying missing translations.

Organizations can extend the translation system with custom terms—internal product names, organization-specific roles, custom process types.

The platform can track which languages users select.

## Accessibility and internationalization

Screen reader users in all languages get natural language descriptions instead of English-only alternatives.

Different languages use different text lengths. German translations are often longer than English. The interface accommodates this expansion without breaking layouts.

The translation architecture can extend to right-to-left languages if needed, though current supported languages all use left-to-right text.

Accessibility conventions vary by locale. The platform can adapt features to match user expectations in different language communities.

## Swiss organizations

Swiss public sector institutions often must provide services in multiple national languages. The platform's four-language support helps meet these requirements without custom development.

Organizations operating across Swiss language regions can deploy a single platform instance. Users in each region see the interface in their preferred language.

Training materials and documentation can be provided in users' native languages.

All four languages work identically. No linguistic community gets a degraded experience.

The translation architecture allows organizations to add languages if needed—regional dialects, languages of immigrant communities, or languages of international branches.

## Technical implementation

Translation files load on-demand. Users only download translations for their selected language.

Translations support parameterized messages. A translation like "Welcome, \{name}!" positions the parameter according to the target language's grammar rules.

The system handles plural forms correctly across languages. Different languages have different pluralization rules.

Locale-aware formatting libraries apply correct formatting rules automatically based on user language selection.

## Maintenance

As interface text changes or new features are added, translations update through coordinated processes.

Users can report translation issues—incorrect terminology, awkward phrasing, missing translations.

Translations periodically undergo professional review by native speakers with technical expertise.

The platform could leverage language models to suggest translation improvements or flag potential inconsistencies.
