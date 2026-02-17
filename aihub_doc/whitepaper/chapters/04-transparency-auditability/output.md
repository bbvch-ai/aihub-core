# Kapitel 04: Plattform-Transparenz und Prüfbarkeit

Eine der grössten Hürden für den produktiven Einsatz generativer KI in Schweizer Unternehmen ist das Problem der
sogenannten «Black-Box». Wenn ein KI-Modell eine Entscheidung trifft, eine Empfehlung ausspricht oder eine Analyse
erstellt, bleibt oft unklar, wie dieses Ergebnis zustande kam. Für regulierte Branchen, die öffentliche Verwaltung und
sicherheitsbewusste Organisationen ist dieser Zustand inakzeptabel. Compliance-Vorgaben, interne Revisionsrichtlinien
und das revidierte Datenschutzgesetz (revDSG) verlangen eine lückenlose Nachvollziehbarkeit.

Der Swiss AI Hub begegnet dieser Herausforderung mit einem fundamentalen Architekturprinzip: Radikale Transparenz durch
einen «White-Box»-Ansatz. Die Plattform wurde so konzipiert, dass technische Abläufe, Datenflüsse und
Entscheidungsketten nicht nur ausgeführt, sondern lückenlos dokumentiert und auditierbar gemacht werden. Damit wird das
Vertrauen in die Technologie durch technische Beweisbarkeit ersetzt.

## Auf einen Blick

- **Lückenlose Kausalkette:** Durch das Swiss AI Agent Protokoll wird jeder logische Schritt eines Agenten als
  unveränderliches Ereignis dokumentiert, was Entscheidungen deterministisch nachvollziehbar macht.
- **Beweisbare Datenherkunft:** Das System verknüpft jede KI-Antwort direkt mit den spezifischen Quell-Dokumenten und
  Text-Chunks in der Wissensdatenbank, um Halluzinationen auditierbar auszuschliessen.
- **Dual-Pipeline Observability:** Eine innovative Architektur trennt tiefes KI-Tracing für Entwickler (Phoenix) von
  operativem Monitoring (SigNoz), um sowohl technische Inspektion als auch stabilen Betrieb zu gewährleisten.
- **Menschliche Letztentscheidung:** Integrierte «Human-in-the-Loop»- und «Bot-in-the-Loop»-Muster ermöglichen es,
  kritische Workflows für menschliche Genehmigungen via Teams oder Slack zu unterbrechen.
- **Messbare Qualität:** Ein integriertes Evaluations-Framework ersetzt subjektive Eindrücke durch objektive Metriken
  wie Korrektheit, Vollständigkeit und Prägnanz basierend auf Test-Datasets.

## Nachvollziehbarkeit von KI-Entscheidungen

### Geschäftlicher Nutzen

In kritischen Geschäftsprozessen reicht ein korrektes Ergebnis allein nicht aus; der Weg dorthin muss erklärbar sein
(«Explainability»). Wenn ein KI-Agent eine medizinische Zusammenfassung erstellt oder einen komplexen Vertrag
analysiert, müssen Fachabteilungen und Auditoren verstehen, welche logischen Schritte durchlaufen wurden. Mangelnde
Erklärbarkeit stellt ein massives Haftungsrisiko dar. Der Swiss AI Hub eliminiert dieses Risiko, indem er die internen
Denkprozesse der KI sichtbar macht. Dies schafft Vertrauen bei den Anwendern und ermöglicht es Compliance-Beauftragten,
die Einhaltung von Richtlinien zu verifizieren, ohne sich auf das blosse Wort der KI verlassen zu müssen.

### Konzeptioneller Ansatz

Die Plattform verabschiedet sich vom Konzept monolithischer, undurchsichtiger Chatbots und setzt stattdessen auf
Workflow-basierte Agenten. Ein Agent folgt keinem Zufallspfad, sondern einem definierten Agenten-Bauplan, der in
einzelne, diskrete Schritte unterteilt ist. Jeder dieser Schritte – sei es das Analysieren einer Eingabe, das Suchen von
Informationen oder das Re-Ranking von Ergebnissen – erzeugt ein unveränderliches Ereignis. Die Summe dieser Ereignisse
bildet einen lückenlosen Pfad, der exakt aufzeigt, was der Agent zu welchem Zeitpunkt getan hat. Durch eine
hierarchische Kontext-Struktur lassen sich dabei komplexe Prozesse logisch gruppieren und bis auf die einzelne
Ausführung hinunterbrechen.

### Technische Umsetzung im Swiss AI Hub

Technisch basiert diese Transparenz auf dem **Swiss AI Agent Protokoll**. Dieses interne Kommunikationsmodell definiert
eine strikte Trennung zwischen Steuerungs- und Anzeigeinformationen mittels typisierter Events, die über NATS JetStream
publiziert werden. **Control Events** steuern die Geschäftslogik und dokumentieren jeden Zustandsübergang im Backend,
während **Display Events** (wie «Gedanken» des Agenten) der Kommunikation mit dem Benutzer dienen.

Jedes Ereignis ist in einer dreistufigen Hierarchie verankert: Der **Thread-Kontext** hält den langfristigen Status
einer Konversation, der **Display-Kontext** gruppiert UI-Interaktionen, und der **Run-Kontext** isoliert die technische
Ausführung eines einzelnen Workflow-Durchlaufs. NATS JetStream stellt dabei sicher, dass diese Ereignisse
revisionssicher gespeichert werden, wobei Administratoren zeit- oder kapazitätsbasierte Limits für die Aufbewahrung
definieren können.

## Revisionssichere Datenherkunft (Data Lineage)

### Geschäftlicher Nutzen

Bei der Nutzung von Retrieval-Augmented Generation (RAG) ist die häufigste Frage von Auditoren: «Woher stammt diese
Information genau?». Halluzinationen – das Erfinden von Fakten durch die KI – stellen ein signifikantes Qualitäts- und
Reputationsrisiko dar. Unternehmen müssen sicherstellen, dass Antworten ausschliesslich auf validierten
Unternehmensdaten basieren. Für rechtliche Prüfungen ist es unerlässlich, beweisen zu können, welche spezifische Version
eines Dokuments zu einem bestimmten Zeitpunkt als Grundlage für eine Auskunft diente. Dies ist insbesondere für
Auskunftsrechte nach revDSG (Art. 25) von zentraler Bedeutung.

### Konzeptioneller Ansatz

Das Konzept der Datenherkunft (Data Lineage) wird im Swiss AI Hub durch eine strikte Referenzierung umgesetzt. Eine
generierte Antwort steht niemals für sich allein, sondern ist untrennbar mit den Quellen verknüpft. Das System
protokolliert nicht nur, dass gesucht wurde, sondern exakt, welche Text-Chunks («Nodes») gefunden und mit welchem
Relevanz-Score sie bewertet wurden. Dies ermöglicht eine Rekonstruktion der Informationsbasis: Auditoren können sehen,
welche Wissensschnipsel dem Modell zur Verfügung standen und ob eventuell veraltete Dokumente berücksichtigt wurden.

### Technische Umsetzung im Swiss AI Hub

Die technische Implementierung nutzt **OpenInference Semantic Conventions**, um RAG-Operationen standardisiert zu
erfassen. Sobald ein Agent die Wissensdatenbank abfragt, wird ein `RetrieverEvent` generiert, das die IDs der
abgerufenen Chunks speichert. In der Benutzeroberfläche des Swiss AI Hub wird dies durch ein Quellenanzeigefeld
visualisiert, das neben der Antwort die exakten Textpassagen, deren Position im Originaldokument sowie die Metadaten
(wie Speicherort und Titel) einblendet. Zusätzlich können **Context Sufficiency Guards** eingesetzt werden, die
technisch prüfen, ob die abgerufenen Informationen ausreichen, um die Frage zu beantworten, und den Prozess bei
ungenügender Datenlage stoppen.

## Enterprise Observability und Monitoring

### Geschäftlicher Nutzen

Eine KI-Plattform darf keine isolierte Insel in der IT-Landschaft sein. Betriebsteams benötigen eine zentrale Sicht auf
die Gesundheit aller Systeme, um Ausfälle proaktiv zu verhindern. Proprietäre Monitoring-Tools führen oft zu Datensilos
und erschweren die Fehleranalyse. CIOs fordern Lösungen, die sich nahtlos in bestehende SIEM- (Security Information and
Event Management) und Monitoring-Landschaften integrieren lassen. Dies sichert die Hoheit über operative Daten und
ermöglicht langfristige Trendanalysen ohne Abhängigkeit von einem spezifischen Anbieter.

### Konzeptioneller Ansatz

Der Swiss AI Hub verfolgt eine Strategie der maximalen Interoperabilität durch offene Standards wie **OpenTelemetry
(OTel)**. OTel fungiert als universelle Sprache für Telemetriedaten und stellt sicher, dass Metriken, Logs und Traces
einheitlich erfasst und korreliert werden. Das Konzept sieht vor, dass der Kunde entscheidet, wohin seine
Telemetriedaten fliessen. Durch einen zentralen Collector werden die Daten gesammelt, gefiltert und an die
entsprechenden Analyse-Systeme weitergeleitet.

### Technische Umsetzung im Swiss AI Hub

Das Herzstück ist der **OpenTelemetry Collector**, der Telemetrie aus allen Containern, Datenbanken und Agenten-Profilen
sammelt und über spezialisierte Pipelines routet. Die Plattform nutzt eine Dual-Backend-Strategie:

1. **KI-Analyse (Phoenix):** Hier fliessen hochdetaillierte Traces für das LLM-Debugging ein, inklusive Token-Nutzung,
   Prompt-Templates und Retrieval-Qualität.
2. **Operations (SigNoz oder externe Systeme):** Hier werden operative Metriken wie CPU-Last, Latenzen und Fehlerraten
   überwacht.

Dank des OTLP-Protokolls kann der Hub ohne Code-Anpassungen an Enterprise-Tools wie Datadog, Splunk oder Dynatrace
angebunden werden. Administratoren können zudem Alarme für kritische Schwellenwerte, wie etwa steigende Fehlerraten oder
das Erreichen von Budgetlimits, konfigurieren.

## Menschliche Kontrolle (Human-in-the-Loop)

### Geschäftlicher Nutzen

Trotz fortschrittlicher Modelle gibt es Entscheidungen, die nicht vollständig automatisiert werden dürfen – sei es aus
ethischen Gründen oder aufgrund regulatorischer Vorschriften. Ein «Human-in-the-Loop»-Prozess verhindert, dass
automatisierte Systeme unkontrolliert agieren, indem er die Effizienz der KI nutzt, aber die Letztentscheidung beim
Menschen belässt. Dies ist besonders bei risikoreichen Aktionen wie dem Auslösen von Zahlungen oder dem Versenden von
Verträgen essenziell. Jede menschliche Interaktion muss dabei ebenso revisionssicher dokumentiert werden wie die
maschinellen Schritte.

### Konzeptioneller Ansatz

Das System integriert den Menschen als aktive Komponente in den Workflow. Ein Prozess kann an definierten Punkten
pausieren und seinen Zustand «einfrieren». Erst wenn eine autorisierte menschliche Interaktion erfolgt – etwa eine
Freigabe oder eine Korrektur – wird der Prozess fortgesetzt. Ein erweitertes Muster ist der **Bot-in-the-Loop**, bei dem
die Eskalation nicht nur in der Plattform-UI, sondern über bestehende Kollaborations-Tools wie Microsoft Teams oder
Slack erfolgt. Dies erlaubt es Experten, Anfragen in ihrer gewohnten Arbeitsumgebung zu bearbeiten, während der KI-Agent
auf die Antwort wartet.

### Technische Umsetzung im Swiss AI Hub

Die Umsetzung erfolgt über asynchrone Ereignismuster im Swiss AI Agent Protokoll. Ein Agent sendet ein
`HumanInTheLoopRequestEvent`, woraufhin der Workflow stoppt und der gesamte Kontext in Redis persistiert wird. Der
**Expert Asking Agent** kann diese Anfrage übernehmen und sie in einen konfigurierten Teams- oder Slack-Kanal posten.
Sobald ein Mensch dort antwortet, erfasst das System dies als `BotInTheLoopResponseEvent`, rehydriert den Agenten und
setzt den Workflow fort. Diese Interaktionen werden lückenlos im Audit-Log festgehalten, inklusive der Identität des
menschlichen Entscheiders.

## Qualitätssicherung und Evaluation

### Geschäftlicher Nutzen

KI-Systeme in der Produktion unterliegen einer ständigen Veränderung – sei es durch neue Dokumente in der
Wissensdatenbank oder durch Updates der Sprachmodelle. «Hoffnung» ist hier keine Strategie; Unternehmen müssen die
Leistung ihrer Agenten objektiv messen können. Regelmässige Evaluationen stellen sicher, dass die Antwortqualität nicht
durch «Model Drift» abnimmt und dass neue Konfigurationen tatsächlich Verbesserungen bringen. Dies dient als technischer
Nachweis der Sorgfaltspflicht gegenüber Regulatoren und Kunden.

### Konzeptioneller Ansatz

Qualität wird im Swiss AI Hub durch systematische Experimente gemessen. Dabei werden Agenten-Profile gegen vordefinierte
Test-Datasets geprüft, die aus Fragen und erwarteten Referenzantworten bestehen. Anstatt sich auf subjektive Stichproben
zu verlassen, nutzt die Plattform den Ansatz «LLM-as-a-Judge»: Unabhängige KI-Modelle bewerten die Antworten des zu
testenden Agenten anhand wissenschaftlich fundierter Metriken. Dies ermöglicht einen automatisierten, vergleichbaren und
auditierbaren Qualitätssicherungsprozess vor jedem Deployment.

### Technische Umsetzung im Swiss AI Hub

Der integrierte **Evaluations-Service** erlaubt die Erstellung von Datasets mit 20 bis 50 Testfällen. Bei der Ausführung
eines Experiments bewerten drei unabhängige Richter-Modelle die Agenten-Antworten in drei Kategorien auf einer Skala von
0 bis 5 Sternen:

- **Korrektheit:** Faktische Genauigkeit gegenüber der Referenzantwort.
- **Vollständigkeit:** Abdeckung aller Aspekte der Anfrage.
- **Prägnanz:** Effizienz der Antwort ohne unnötige Abschweifungen.

Die Ergebnisse werden in einem Dashboard visualisiert, das Gesamtmetriken sowie eine detaillierte Aufschlüsselung pro
Frage zeigt. Dies ermöglicht es Entwicklern, gezielt Wissenslücken oder Schwächen in den Agenten-Bauplänen zu
identifizieren und zu beheben, bevor ein Agent produktiv gesetzt wird.

## Finanzielle Transparenz und Kostenkontrolle

### Geschäftlicher Nutzen

Die Abrechnungsmodelle grosser Sprachmodelle (Pay-per-Token) bergen erhebliche finanzielle Risiken. Eine fehlerhafte
Schleife oder exzessive Nutzung kann Budgets in kürzester Zeit sprengen. CFOs benötigen Echtzeit-Transparenz und harte
Limits («Circuit Breakers»), um die Kosten pro Abteilung, Projekt oder Benutzer steuern zu können. Dies bildet die
Grundlage für eine verursachergerechte interne Leistungsverrechnung (Chargeback) und verhindert unvorhergesehene
Kostenexplosionen.

### Konzeptioneller Ansatz

Kostenkontrolle ist im Swiss AI Hub direkt in das LLM-Gateway integriert. Jede Interaktion wird vermessen, bewertet und
einem Mandanten oder Benutzer zugeordnet. Das System unterscheidet zwischen verschiedenen Kostenarten (Prompt-,
Completion- und Embedding-Tokens) und wendet vordefinierte Regeln an. Durch die Definition von Quotas und
Ratenbegrenzungen wird sichergestellt, dass die Ressourcennutzung innerhalb der definierten Leitplanken bleibt.

### Technische Umsetzung im Swiss AI Hub

Das **LLM-Gateway** agiert als zentraler Wächter und setzt Limits technisch durch Umgebungsvariablen wie
`LITE_LLM_PROXY_USER_MAX_BUDGET` durch. Administratoren können sowohl harte Obergrenzen als auch «Soft Budgets»
(Warnschwellen) definieren. Zusätzlich können Limits für Tokens pro Minute (TPM) oder Anfragen pro Minute (RPM) gesetzt
werden, um Missbrauch oder Amok laufende Skripte sofort zu stoppen. Jeder Aufruf erzeugt zudem ein `LLMCostEvent`, das
in Echtzeit-Dashboards einfliesst und detaillierte Reports über die Wirtschaftlichkeit der verschiedenen
KI-Anwendungsfälle ermöglicht.
