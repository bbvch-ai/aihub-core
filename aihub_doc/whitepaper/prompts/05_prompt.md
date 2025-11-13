# Kapitel 05: Transparente und Auditierbare AI-Agents

## Kapitelziel
Erklären Sie, wie sich Swiss AI-Hub Agents von "Black-Box-AI" unterscheiden und warum Transparenz und Nachvollziehbarkeit für Unternehmen wichtig sind (1300-1800 Wörter).

**WICHTIG**: Folgen Sie den Richtlinien in `general_prompt.md` für Textfluss, Struktur und Business-Fragen. Dieses Kapitel ist **lang** (1300-1800 Wörter).


## Business-Dimensionen (Priorität für dieses Kapitel)
1. **DATENSCHUTZ** - SEHR WICHTIG: Transparenz, Auditierbarkeit (revDSG)
2. **SICHERHEIT** - Wichtig: Workflow-Kontrolle, Nachvollziehbarkeit
3. **ZUKUNFTSSICHERHEIT** - Wichtig: Erweiterbarkeit, Custom Workflows

**Behandeln Sie diese Dimensionen explizit** mit konkreten Antworten auf Business-Fragen.

## Hauptthemen

### 5.1 Workflow-basierte Agent-Architektur
- Strukturierte Workflows statt autonomer Tool-Auswahl
- Transparente Ausführung: Jeder Schritt sichtbar und auditierbar
- Nachvollziehbares Reasoning: "Denkprozess" der KI einsehbar
- Deterministische Schritte: Viele Operationen ohne LLM (Datenvalidierung, Formatierung)
- Workflow kontrolliert Ausführung: Agent kann nicht auf unautorisierten Zugriff oder Aktionen zugreifen

**Geschäftlicher Nutzen**: Vertrauen, Compliance, Audit-Bereitschaft, Risikominderung

### 5.2 Eingebaute Agent-Fähigkeiten
- RAG Agents: Frage-Antwort mit Unternehmenswissen und Quellenangaben
- Expert-Asking Agents: Multi-Agent-Kollaboration
- Conversational Agents: Natürlichsprachige Interaktion mit Kontext
- Tool-Using Agents: Zugriff auf externe Systeme und APIs

**Geschäftlicher Nutzen**: Sofortige Produktivität, keine Custom-Entwicklung für gängige Szenarien

### 5.3 Human-in-the-Loop (HITL)
- Approval-Workflows: Agent pausiert und fordert menschliche Genehmigung an
- Kontext-Erhaltung: Workflow setzt sich mit vollem Gedächtnis fort
- Flexible Wartezeiten: Sekunden, Minuten, Stunden oder Tage
- Vollständiger Audit-Trail: Jede Interaktion protokolliert
- Use Cases: Regulatorische Genehmigungen, Qualitätsprüfungen, Consent-Workflows

**Geschäftlicher Nutzen**: Schrittweise Automatisierung, Risikomanagement, Compliance, menschliche Kontrolle

### 5.4 Responsible AI Features
- Halluzinations-Minderung: Quellenangaben, Retrieval-Grounding, Confidence Scores
- Confidence-Indikatoren: KI zeigt Unsicherheitslevel
- Datenqualität-Handling: Erkennt und managt fehlende, widersprüchliche oder fehlerhafte Daten
- Rückfragen-Fähigkeit: Agent stellt klärende Fragen bei Unsicherheit
- Fehlererkennung: Hebt potenzielle Probleme in Eingabedaten hervor

**Geschäftlicher Nutzen**: Vertrauenswürdige KI, Risikoreduktion, Qualitätssicherung

### 5.5 Agent Governance
- Vordefinierte Antworten: Konfigurierbare Antworten auf spezifische Fragen/Keywords
- Prompt Engineering: Domänenspezifische Anpassung (z.B. Schweizer Rechtssprache, Behördenterminologie)
- Input-Validierung: Guards verhindern bösartige oder unangemessene Eingaben
- Output-Qualitätsprüfung: Validierung der Agent-Antworten vor Auslieferung
- Versionierung: Alle Agent-Versionen nachvollziehbar

**Geschäftlicher Nutzen**: Konsistente Antworten, Domänen-Expertise, Qualitätskontrolle

## Kernfragen, die Leser beantworten möchten

### Transparenz und Nachvollziehbarkeit
1. Wie kann ich nachvollziehen, was ein AI-Agent tut und warum?
2. Was unterscheidet transparente Agents von "Black-Box"-KI?
3. Kann ich jeden Schritt eines Agent-Workflows einsehen und auditieren?
4. Wie dokumentiert die Plattform KI-Entscheidungen für Compliance und Audits?

### Agent-Fähigkeiten
5. Welche Arten von Agents sind out-of-the-box verfügbar?
6. Kann ein Agent Fragen mit Bezug auf Unternehmenswissen beantworten?
7. Können mehrere spezialisierte Agents zusammenarbeiten?
8. Wie integrieren sich Agents mit externen Systemen?

### Human-in-the-Loop
9. Wie stelle ich sicher, dass kritische Entscheidungen von Menschen überprüft werden?
10. Kann ein Agent pausieren und auf menschliche Genehmigung warten?
11. Wie lange kann ein Workflow auf menschliches Feedback warten?
12. Wird jede menschliche Interaktion protokolliert?
13. Für welche Use Cases ist Human-in-the-Loop sinnvoll?

### Responsible AI
14. Wie verhindert die Plattform, dass die KI falsche Informationen ("Halluzinationen") generiert?
15. Kann die KI ihren Unsicherheitsgrad mitteilen?
16. Wie geht die KI mit fehlenden, fehlerhaften oder widersprüchlichen Daten um?
17. Stellt die KI Rückfragen, wenn sie sich unsicher ist?
18. Wie wird erkannt, ob Eingabedaten Probleme enthalten?

### Governance und Kontrolle
19. Kann ich vordefinierte Antworten auf häufige Fragen hinterlegen?
20. Wie kann ich die KI an unsere Fachsprache (z.B. Schweizer Rechtssprache) anpassen?
21. Wie verhindere ich, dass Benutzer unangemessene Eingaben machen?
22. Wie stelle ich die Qualität der Agent-Antworten sicher?
23. Kann ich verschiedene Versionen eines Agents verwalten und zurückrollen?

### Anpassung und Erweiterung
24. Kann ich domänenspezifische Agents für meine Branche erstellen?
25. Wie kombiniere ich KI mit regelbasierten Systemen (z.B. für Compliance)?
26. Kann die KI plausible nächste Schritte in Prozessen vorschlagen?
