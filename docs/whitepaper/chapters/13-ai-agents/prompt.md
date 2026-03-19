# Kapitel 13: AI-Agenten und Kernkonzepte

## Kapitelziel

Dieses Kapitel erläutert die Notwendigkeit einer transparenten und steuerbaren Agenten-Architektur als Gegenentwurf zu
intransparenten Black-Box-Modellen. Es wird dargelegt, wie durch workflow-basierte Abläufe und deterministische
Prozessschritte die für den öffentlichen Sektor kritische Nachvollziehbarkeit und Revisionssicherheit gewährleistet
wird. Der Abschnitt beschreibt zudem, wie spezialisierte Agenten-Typen sicher in bestehende Informationssysteme
integriert werden, um komplexe Aufgaben unter Einhaltung strenger Governance-Vorgaben zu lösen. Ein zentraler Fokus
liegt auf Mechanismen zur Qualitätssicherung, einschliesslich optionaler menschlicher Prüfschritte und Strategien zur
Vermeidung von Halluzinationen (Responsible AI). Ziel ist es, ein Verständnis für den Aufbau vertrauenswürdiger,
auditierbarer KI-Systeme zu schaffen, die hohen Compliance-Standards genügen.

## Kernaussagen

- Deterministische Workflow-Steuerung: Anstelle intransparenter „Black-Box“-Entscheidungen nutzt die Plattform eine
  Workflow-basierte Architektur, die durch definierte, deterministische Prozessschritte ein vorhersehbares und
  kontrollierbares Verhalten der KI-Agenten garantiert.
- Spezialisierung und Integration: Das System setzt auf spezialisierte Agenten-Typen (wie RAG-Agenten), die über
  gesicherte Schnittstellen nahtlos in bestehende Fachanwendungen integriert werden, um komplexe Aufgaben unter
  Berücksichtigung des spezifischen Kontextes zu lösen.
- Menschliche Kontrollinstanz (Human-in-the-Loop): Für kritische Entscheidungsprozesse sind Unterbrechungsmechanismen
  implementiert, die es Agenten ermöglichen, Arbeitsabläufe für eine menschliche Validierung oder Genehmigung
  anzuhalten, ohne den logischen Kontext zu verlieren.
- Lückenlose Nachvollziehbarkeit: Sämtliche „Reasoning“-Schritte, Systemaufrufe und genutzte Datenquellen eines Agenten
  werden detailliert protokolliert, um eine vollständige Auditierbarkeit zu gewährleisten und regulatorischen
  Anforderungen gerecht zu werden.
- Qualitätssicherung und Halluzinationsvermeidung: Durch domänenspezifisches Prompt-Engineering und strikte
  Input-Validierungen wird der Lösungsraum der Agenten auf verifizierte Fakten beschränkt, wodurch das Risiko von
  Halluzinationen und fehlerhaften Ausgaben minimiert wird.
- Sichere Orchestrierung: Die Architektur regelt die Zusammenarbeit mehrerer Agenten (Multi-Agenten-Systeme) durch
  strikte Governance-Vorgaben, die verhindern, dass automatisierte Prozesse unautorisierte Aktionen ausführen oder
  Berechtigungsgrenzen überschreiten.

## Umfang

max. 900 Wörter, 3 Seiten

## Business-Fragen, die das Kapitel beantwortet

- Was unterscheidet Swiss AI Hub Agents von Black-Box-AI-Systemen?
- Was bedeutet "Workflow-basierte Architektur"?
- Warum ist das sicherer als autonome Tool-Auswahl?
- Wie wird verhindert, dass Agenten unautorisierte Aktionen durchführen?
- Was sind deterministische Schritte und warum sind sie wichtig?
- Welche Agententypen sind integriert?
- Was sind RAG-Agenten?
- Wie funktioniert Multi-Agenten-Kollaboration?
- Können Agenten auf externe Systeme zugreifen?
- Sind Agenten konversationsfähig mit Kontext?
- Wie funktionieren Human-in-the-Loop-Mechanismen?
- Können Agenten auf menschliche Genehmigung warten?
- Wird der Kontext bei Wartezeiten bewahrt?
- Wie lange können Wartezeiten sein (Sekunden, Stunden, Tage)?
- Werden alle menschlichen Interaktionen protokolliert?
- Wie werden Agenten gesteuert und kontrolliert?
- Können vordefinierte Antworten konfiguriert werden?
- Wie funktioniert Prompt-Engineering für Domänen (z.B. Schweizer Recht)?
- Gibt es Input-Validierung gegen bösartige Eingaben?
- Wie wird Output-Qualität geprüft?
- Sind Agenten versioniert?
- Kann ich nachvollziehen, wie ein Agent zu einer Entscheidung kam?
- Werden LLM-Aufrufe mit Prompts und Responses geloggt?
- Kann ich sehen, welche Dokumente durchsucht wurden?
- Wird Tool-Nutzung getrackt?
- Werden Kosten pro Agent-Execution erfasst?
- Wie wird gegen Halluzinationen vorgegangen?
- Gibt es Confidence-Scores für Agent-Antworten?
- Wird Bias erkannt und gemeldet?
- Wie wird Model-Drift überwacht?
- Wie wird Nutzer-Feedback zur Verbesserung genutzt?
