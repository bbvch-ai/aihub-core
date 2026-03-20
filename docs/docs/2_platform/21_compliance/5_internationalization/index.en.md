---
title: Internationalization
---

# Internationalization

The platform supports Switzerland's four national languages: German, English, French, and Italian. Users can work in
their preferred language throughout the interface.

## Language support

German serves as the default language, but all four languages work identically. The interface, error messages, help
text, and navigation all include translations.

All user-facing text has translations - form validation, dialogs, notifications, error messages, help documentation, and
instructions. Users see no untranslated elements or mixed languages.

Dynamically generated content also respects language preferences. Service descriptions, agent names, and knowledge
namespace labels adapt to the selected language.

Users select their language during authentication or in profile settings. The selection persists across sessions.

## Language selection and switching

Users configure their language in their profile. This becomes the default for all sessions across devices.

Users can temporarily switch languages for a specific session. This helps multilingual users who prefer different
languages for different tasks.

Language changes apply immediately without reloading the page. All text updates instantly.

URLs don't include language codes. Shared links show content in the recipient's preferred language, not the sender's.

## Translation quality

The platform maintains consistent terminology across all languages. Common terms like "agent," "thread," "namespace,"
and "process" use the same translations throughout the interface.

Specialized terminology for technical AI concepts and Swiss regulatory terms receives appropriate translations for each
language.

If a translation is missing in the selected language, the platform falls back to German.

## Localized content handling

User-created resources can include translations for all supported languages. Administrators can provide a knowledge
namespace name and description in German, English, French, and Italian.

The system can automatically detect document language for processing and knowledge management. This enables
language-specific search optimization and retrieval.

Numbers, dates, times, and currencies format according to locale conventions. German users see dates as "31.12.2024,"
while English users see "12/31/2024."

Search functionality uses language-specific tokenization and stemming. German searches use German linguistic rules,
French searches use French rules.

## Custom translations

Organizations can add custom translations for organization-specific terms like internal product names, custom roles, or
specialized process types. Administrators can modify translations through the platform's administrative interface.

## Accessibility and internationalization

Screen reader users in all languages get natural language descriptions instead of English-only alternatives.

Different languages use different text lengths. German translations are often longer than English. The interface
accommodates this expansion without breaking layouts.

The translation architecture can extend to right-to-left languages if needed, though current supported languages all use
left-to-right text.

Accessibility conventions vary by locale. The platform can adapt features to match user expectations in different
language communities.

## Swiss organizations

Swiss public sector institutions often must provide services in multiple national languages. The platform's
four-language support helps meet these requirements without custom development.

Organizations operating across Swiss language regions can deploy a single platform instance. Users in each region see
the interface in their preferred language.

Training materials and documentation can be provided in users' native languages.

All four languages work identically. No linguistic community gets a degraded experience.

The translation architecture allows organizations to add languages if needed - regional dialects, languages of immigrant
communities, or languages of international branches.
