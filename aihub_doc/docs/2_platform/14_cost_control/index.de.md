---
title: Kostenkontrolle
source_sha: ca5267e7f0332015d3f974f6edf986fd61bad8a1a9bdee6ce2e907df9d025b8b
---

# Kostenkontrolle

KI-Agenten verursachen Betriebskosten. Der AI-Hub verfolgt diese Kosten, damit Sie Ausgaben optimieren, Investitionen
rechtfertigen und Budgets prognostizieren können.

## Funktionsweise der KI-Kosten

KI-Anbieter berechnen Kosten basierend auf der Token-Nutzung. Tokens sind kleine Textblöcke (ungefähr 4 Zeichen), die
Modelle verarbeiten.

Kostenmodell-Vergleich:

| Modell              | Typ                | Kostenstruktur                                                                                                                                                                   |
| :------------------ | :----------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| API (Pay-per-Token) | Variable OPEX      | Zahlung an Anbieter (OpenAI, Google) für jedes verarbeitete Token                                                                                                                |
| Lokal gehostet      | CAPEX + Feste OPEX | Kapitalausgaben für Hardware (GPUs, Server) plus laufende Kosten für Strom und MLOps-Personal. Die Kosten pro Token betragen \$0, aber die festen Infrastrukturkosten sind hoch. |

Jede Interaktion verbraucht verschiedene Arten von Tokens zu unterschiedlichen Preisen:

::: details Prompt-Tokens
Ihre Eingabe an die KI, einschließlich Fragen, Gesprächsverlauf, System-Prompts und abgerufene Dokumente. Längere
Prompts kosten mehr.
:::

::: details Completion-Tokens
Die von der KI generierten Antworten. Längere, detailliertere Antworten kosten mehr.
:::

::: details Embedding-Tokens
Dokumentenverarbeitung für Suche und Abruf. Typischerweise günstiger als Textgenerierung.
:::

::: details Modell-Stufen
| Stufe       | Beispiele  | Anwendungsfall                                         | Kosten     |
| :---------- | :--------- | :----------------------------------------------------- | :--------- |
| Flaggschiff | GPT-5      | Komplexe Argumentation, Aufgaben mit hoher Genauigkeit | Höchste    |
| Ausgewogen  | GPT-5 mini | Standard-Workflows, interne Assistenten                | Mittel     |
| Effizient   | GPT-5 nano | Einfache Aufgaben mit hohem Volumen, Klassifizierung   | Niedrigste |
:::

## Kostenverfolgung

Der AI-Hub verfolgt die Kosten für jede Konversation. Wenn Sie mit einem Agenten chatten, zeichnet die Plattform die
Token-Nutzung auf und berechnet die Kosten. Diese Informationen werden im Konversationsverlauf angezeigt.

Das Tracking funktioniert für alle KI-Modelle, unabhängig davon, ob Sie Cloud-Dienste wie OpenAI oder selbst gehostete
Modelle verwenden. Für selbst gehostete Modelle können Sie einen Kostenwert zuweisen, um Ausgaben konsistent zu
verfolgen.

Sie können Kosteninformationen pro Konversation anzeigen, um zu sehen, welche Fragen am teuersten sind. Dies hilft bei
Entscheidungen zum Agenten-Design, zur Modellauswahl und zur Budgetplanung.

## Budgets und Ratenbegrenzungen

::: warning Derzeit nicht konfiguriert
Budget- und Ratenbegrenzungsfunktionen existieren, sind aber standardmäßig nicht aktiviert. Diese Funktion wurde noch
nicht getestet.
:::

Die Plattform kann Ausgabenlimits und Nutzungsbeschränkungen durchsetzen. Bei Aktivierung können Administratoren
festlegen:

- Budgetobergrenzen: Blockiert Anfragen, wenn Benutzer die Ausgabenlimits überschreiten
- Nutzungswarnungen: Benachrichtigt, wenn Budgetschwellenwerte erreicht werden
- Ratenbegrenzungen: Steuert, wie viele Anfragen oder Tokens Benutzer pro Minute verbrauchen können
- Limits für gleichzeitige Anfragen: Beschränkt simultane KI-Operationen

Diese Kontrollen erfordern eine Umgebungskonfiguration während des Deployments.

## Optimierungsstrategien

### Modellauswahl

Passen Sie die Modellstufe Ihrer Aufgabe an. Verwenden Sie Flaggschiff-Modelle (GPT-5) für komplexe, kundenorientierte
oder hochpräzise Aufgaben. Verwenden Sie ausgewogene Modelle (GPT-5 mini) für interne Assistenten oder
Standard-Workflows. Verwenden Sie effiziente Modelle (GPT-5 nano) für Klassifizierungen, Datenextraktionen oder
hochfrequenten Chat.

### Lokal gehostete Modelle

Lokales Hosting verlagert die Ausgaben von variablen Pay-per-Token-Gebühren auf feste Infrastrukturkosten.
Organisationen wählen dies aus Gründen des Datenschutzes (HIPAA, GDPR), der Compliance und des IP-Schutzes, nicht wegen
sofortiger Kosteneinsparungen. Es erfordert Kapitalinvestitionen (GPUs, Server) und laufende Betriebskosten (Strom,
MLOps-Personal).
