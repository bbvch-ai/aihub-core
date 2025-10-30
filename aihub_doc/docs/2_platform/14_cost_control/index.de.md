---
title: Kostenkontrolle
source_sha: db5a62ad0f04b20a4689e5b23cd1ef5591cfb0609d82a8f4be0a4dee34cbf074
---

# Kostenkontrolle

Der Betrieb von KI-Agenten ist mit Kosten verbunden. Der AI-Hub verfolgt diese Kosten, damit Sie Ausgaben optimieren,
Investitionen rechtfertigen und Budgets prognostizieren können.

## Wie KI-Kosten funktionieren

KI-Anbieter berechnen Kosten basierend auf der Token-Nutzung. Tokens sind kleine Textabschnitte (ungefähr 4 Zeichen),
die Modelle verarbeiten.

Vergleich der Kostenmodelle:

| Modell              | Typ                | Kostenstruktur                                                                                                                                                                   |
| ------------------- | ------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| API (Pay-per-token) | Variable OPEX      | Zahlen Sie Anbietern (OpenAI, Google) für jedes verarbeitete Token                                                                                                               |
| Lokal gehostet      | CAPEX + Feste OPEX | Kapitalausgaben für Hardware (GPUs, Server) plus laufende Kosten für Strom und MLOps-Personal. Die Kosten pro Token betragen 0 \$, aber die festen Infrastrukturkosten sind hoch |

Jede Interaktion verbraucht verschiedene Arten von Tokens zu unterschiedlichen Preispunkten:

::: details Prompt-Tokens
Ihre Eingabe an die KI, einschließlich Fragen, Gesprächsverlauf, System-Prompts und abgerufener Dokumente. Längere
Prompts kosten mehr.
:::

::: details Completion-Tokens
Die von der KI generierten Antworten. Längere, detailliertere Antworten kosten mehr.
:::

::: details Embedding-Tokens
Dokumentenverarbeitung für Suche und Abruf. Typischerweise günstiger als Textgenerierung.
:::

::: details Modell-Tiers
| Tier      | Beispiele  | Anwendungsfall                                       | Kosten         |
| --------- | ---------- | ---------------------------------------------------- | -------------- |
| Flagship  | GPT-5      | Komplexe Schlussfolgerungen, hochpräzise Aufgaben    | Am höchsten    |
| Balanced  | GPT-5 mini | Standard-Workflows, interne Assistenten              | Mittel         |
| Efficient | GPT-5 nano | Einfache Aufgaben mit hohem Volumen, Klassifizierung | Am niedrigsten |
:::

## Kostenverfolgung

Der AI-Hub verfolgt die Kosten für jede Konversation. Wenn Sie mit einem Agenten chatten, erfasst die Plattform die
Token-Nutzung und berechnet die Kosten. Diese Informationen erscheinen im Konversationsverlauf.

Das Tracking funktioniert für alle KI-Modelle, egal ob Sie Cloud-Dienste wie OpenAI oder selbst gehostete Modelle
verwenden. Bei selbst gehosteten Modellen können Sie einen Kostenwert zuweisen, um die Ausgaben konsistent zu verfolgen.

Sie können Kosteninformationen pro Konversation einsehen, um zu sehen, welche Fragen am teuersten sind. Dies hilft bei
Agenten-Designentscheidungen, Modellauswahl und Budgetplanung.

## Budgets und Ratenbegrenzungen

::: warning Derzeit nicht konfiguriert
Budget- und Ratenbegrenzungsfunktionen existieren, sind aber standardmäßig nicht aktiviert. Diese Funktion wurde noch
nicht getestet.
:::

Die Plattform kann Ausgabenlimits und Nutzungsbeschränkungen durchsetzen. Wenn aktiviert, können Administratoren
festlegen:

- Budgetobergrenzen: Blockiert Anfragen, wenn Benutzer Ausgabenlimits überschreiten
- Nutzungsalarme: Benachrichtigt, wenn Budgetschwellenwerte erreicht werden
- Ratenbegrenzungen: Steuert, wie viele Anfragen oder Tokens Benutzer pro Minute verbrauchen können
- Begrenzungen für gleichzeitige Anfragen: Beschränkt simultane KI-Operationen

Diese Kontrollen erfordern eine Umgebungskonfiguration während der Bereitstellung.

## Optimierungsstrategien

### Modellauswahl

Passen Sie den Modell-Tier an Ihre Aufgabe an. Verwenden Sie Flagship-Modelle (GPT-5) für komplexe, kundenorientierte
oder hochpräzise Aufgaben. Verwenden Sie Balanced-Modelle (GPT-5 mini) für interne Assistenten oder Standard-Workflows.
Verwenden Sie effiziente Modelle (GPT-5 nano) für Klassifizierung, Datenextraktion oder häufigen Chat.

### Lokal gehostete Modelle

Lokales Hosting verlagert die Ausgaben von variablen Pro-Token-Gebühren auf feste Infrastrukturkosten. Organisationen
wählen dies aus Gründen des Datenschutzes (HIPAA, GDPR), der Compliance und des IP-Schutzes, nicht wegen sofortiger
Kosteneinsparungen. Es erfordert Kapitalinvestitionen (GPUs, Server) und laufende Betriebskosten (Strom,
MLOps-Personal).
