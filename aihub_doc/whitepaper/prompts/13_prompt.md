# Kapitel 13: AI-Agenten und Kernkonzepte

## Kapitelziel
Erklären Sie, wie sich Swiss AI-Hub Agents von Black-Box-AI unterscheiden und warum Workflow-basierte Transparenz für Unternehmen kritisch ist (900 Wörter, 3 Seiten).

**WICHTIG**: Folgen Sie den Richtlinien in `general_prompt.md` für Textfluss, Struktur und Business-Fragen. Dieses Kapitel ist **mittel** (900 Wörter).

## Business-Dimensionen (Priorität für dieses Kapitel)
1. **DATENSCHUTZ** - SEHR WICHTIG: Transparenz, Auditierbarkeit, Erklärbarkeit für revDSG/AI Act
2. **SICHERHEIT** - Wichtig: Workflow-Kontrolle, Nachvollziehbarkeit, keine autonome Tool-Auswahl
3. **ZUKUNFTSSICHERHEIT** - Wichtig: Erweiterbarkeit, Custom Workflows, keine Black-Box-Abhängigkeit

**Behandeln Sie diese Dimensionen explizit** mit konkreten Antworten auf Business-Fragen.

## Themen und Inhalte

Beschreiben Sie folgende Agent-Konzepte und deren geschäftlichen Nutzen:

- **Workflow-basierte Agenten-Architektur (vs. Black-Box)**: Strukturierte, vordefinierte Operationssequenzen statt autonomer Tool-Auswahl; jeder Schritt sichtbar, nachvollziehbar, prüfbar; Workflows kontrollieren Ausführung und verhindern unautorisierte Zugriffe/Aktionen; deterministische Schritte (viele Operationen ohne LLM für Zuverlässigkeit und Kostenreduktion)
- **Integrierte Agententypen**: RAG-Agenten (Frage-Antwort mit Unternehmenswissen und Quellenangaben), Expert-Asking-Agenten (Multi-Agenten-Kollaboration), Conversational-Agenten (natürlichsprachige Interaktion mit Kontextbewahrung), Tool-Using-Agenten (Zugriff auf externe Systeme und APIs)
- **Agenten-Fähigkeiten**: Rückfragen bei Unsicherheit, Handhabung von Datenqualitätsproblemen, Confidence-Indicators, Kombination mit regelbasierten Systemen (Compliance-Sicherheit durch harte Regeln), Human-in-the-Loop-Mechanismen (Approval-Workflows, Kontext-Erhaltung, flexible Wartezeiten, vollständige Audit-Trails)
- **Agenten-Governance**: Vordefinierte Antworten für spezifische Fragen/Keywords, Prompt-Engineering (Domänen-spezifische Anpassung, z.B. Schweizer Rechtssprache), Input-Validierung (Guards gegen bösartige Eingaben), Output-Qualitätsprüfung, Versionierung
- **Transparenz-Features**: Vollständiger "Denkprozess" sichtbar, LLM-Aufrufe mit Prompts und Responses, Retriever-Events (welche Dokumente durchsucht), Tool-Usage-Tracking, Kosten-Tracking pro Agent-Execution
- **Responsible AI Features**: Hallucination-Mitigation (Quellenangaben, Retrieval-Grounding, Confidence-Scores), Bias-Detection, Model-Drift-Tracking, Quality-Feedback-Loops

Fokussieren Sie auf den fundamentalen Unterschied zu Black-Box-AI: Transparenz, Kontrolle und Erklärbarkeit für Enterprise- und Public-Sector-Einsatz.

## Business-Fragen, die das Kapitel beantwortet

**ERINNERUNG**: Alle technischen Details müssen am ENDE des Kapitels stehen, klar gekennzeichnet als "Technischer Exkurs" oder "Technische Umsetzung".

1. Was unterscheidet Swiss AI-Hub Agents von Black-Box-AI-Systemen?
2. Was bedeutet "Workflow-basierte Architektur"?
3. Warum ist das sicherer als autonome Tool-Auswahl?
4. Wie wird verhindert, dass Agenten unautorisierte Aktionen durchführen?
5. Was sind deterministische Schritte und warum sind sie wichtig?

6. Welche Agententypen sind integriert?
7. Was sind RAG-Agenten?
8. Wie funktioniert Multi-Agenten-Kollaboration?
9. Können Agenten auf externe Systeme zugreifen?
10. Sind Agenten konversationsfähig mit Kontext?

11. Wie funktionieren Human-in-the-Loop-Mechanismen?
12. Können Agenten auf menschliche Genehmigung warten?
13. Wird der Kontext bei Wartezeiten bewahrt?
14. Wie lange können Wartezeiten sein (Sekunden, Stunden, Tage)?
15. Werden alle menschlichen Interaktionen protokolliert?

16. Wie werden Agenten gesteuert und kontrolliert?
17. Können vordefinierte Antworten konfiguriert werden?
18. Wie funktioniert Prompt-Engineering für Domänen (z.B. Schweizer Recht)?
19. Gibt es Input-Validierung gegen bösartige Eingaben?
20. Wie wird Output-Qualität geprüft?
21. Sind Agenten versioniert?

22. Kann ich nachvollziehen, wie ein Agent zu einer Entscheidung kam?
23. Werden LLM-Aufrufe mit Prompts und Responses geloggt?
24. Kann ich sehen, welche Dokumente durchsucht wurden?
25. Wird Tool-Nutzung getrackt?
26. Werden Kosten pro Agent-Execution erfasst?

27. Wie wird gegen Halluzinationen vorgegangen?
28. Gibt es Confidence-Scores für Agent-Antworten?
29. Wird Bias erkannt und gemeldet?
30. Wie wird Model-Drift überwacht?
31. Wie wird Nutzer-Feedback zur Verbesserung genutzt?
