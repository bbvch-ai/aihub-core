---
title: Kostenkontrolle
source_sha: "cf794b0668f6689edbabc34314e15bae51b0ffae539f87051c864997f144fb0b"
---

# Kostenkontrolle

KI-Agents verursachen Betriebskosten. Der Swiss AI Hub verfolgt diese Kosten, damit Sie Ausgaben optimieren, Investitionen rechtfertigen und Budgets prognostizieren können.

## Wie KI-Kosten funktionieren

KI-Anbieter berechnen Kosten basierend auf der Token-Nutzung. Tokens sind kleine Textabschnitte (ungefähr 4 Zeichen), die Modelle verarbeiten.

Kostenmodell-Vergleich:

| Modell            | Typ                | Kostenstruktur                                                                                                                                              |
| :---------------- | :----------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| API (Pay-per-token) | Variable OPEX      | Bezahlen Sie Anbieter (OpenAI, Google) für jedes verarbeitete Token                                                                                         |
| Lokal gehostet    | CAPEX + Feste OPEX | Investitionskosten für Hardware (GPUs, Server) plus laufende Kosten für Strom und MLOps-Personal. Die Kosten pro Token betragen $0, aber die festen Infrastrukturkosten sind hoch |

Jede Interaktion verbraucht verschiedene Arten von Tokens zu unterschiedlichen Preisen:

::: details Prompt-Tokens
Ihre Eingabe an die KI, einschliesslich Fragen, Gesprächsverlauf, System-Prompts und abgerufener Dokumente. Längere Prompts kosten mehr.
:::

::: details Completion-Tokens
Die von der KI generierten Antworten. Längere, detailliertere Antworten kosten mehr.
:::

::: details Embedding-Tokens
Dokumentenverarbeitung für Suche und Abruf. Typischerweise günstiger als Textgenerierung.
:::

::: details Modellstufen
| Stufe     | Beispiele  | Anwendungsfall                                   | Kosten      |
| :-------- | :--------- | :----------------------------------------------- | :---------- |
| Flagship  | GPT-5      | Komplexe Schlussfolgerungen, Aufgaben mit hoher Genauigkeit | Höchste     |
| Balanced  | GPT-5 mini | Standard-Workflows, interne Assistenten          | Mittel      |
| Efficient | GPT-5 nano | Einfache Aufgaben mit hohem Volumen, Klassifizierung | Niedrigste |
:::

## Kostenverfolgung

Der Swiss AI Hub verfolgt die Kosten für jede Konversation. Wenn Sie mit einem Agent chatten, zeichnet die Plattform die Token-Nutzung auf und berechnet die Kosten. Diese Informationen erscheinen im Konversations-Thread.

Die Verfolgung funktioniert für alle KI-Modelle, unabhängig davon, ob Sie Cloud-Services wie OpenAI oder selbst gehostete Modelle verwenden. Für selbst gehostete Modelle können Sie einen Kostenwert zuweisen, um die Ausgaben konsistent zu verfolgen.

Sie können Kosteninformationen pro Konversation anzeigen, um zu sehen, welche Fragen am teuersten sind. Dies hilft bei Agent-Design-Entscheidungen, der Modellwahl und der Budgetplanung.

## Budgets und Ratenbegrenzungen

LiteLLM bietet pro Benutzer Budget- und Ratenbegrenzungsfunktionen über sein Benutzerverwaltungssystem. Diese Kontrollen werden über Umgebungsvariablen konfiguriert und automatisch vom Proxy durchgesetzt.

Verfügbare Kontrollen:

- Max. Budget: Harte Obergrenze für Ausgaben pro Benutzer innerhalb eines Budgetzeitraums. Blockiert Anfragen bei Überschreitung.

- Soft Budget: Warnschwelle, die Benachrichtigungen auslöst, ohne Anfragen zu blockieren.

- Budgetdauer: Zeitraum für die Budgetrücksetzung (z.B. "30d" für monatliche Budgets). Ohne diese werden Budgets nie zurückgesetzt.

- TPM-Limit: Maximale Tokens pro Minute, die ein Benutzer verbrauchen kann.

- RPM-Limit: Maximale Anfragen pro Minute, die ein Benutzer stellen kann.

- Max. parallele Anfragen: Maximale gleichzeitige Anfragen, die ein Benutzer aktiv haben kann.

::: details Konfiguration über Umgebungsvariablen
```bash
LITE_LLM_PROXY_USER_MAX_BUDGET=100.0           # $100 hard limit
LITE_LLM_PROXY_USER_SOFT_BUDGET=80.0           # Alert at $80
LITE_LLM_PROXY_USER_BUDGET_DURATION="30d"      # Reset monthly
LITE_LLM_PROXY_USER_TPM_LIMIT=10000            # 10k tokens/minute
LITE_LLM_PROXY_USER_RPM_LIMIT=60               # 60 requests/minute
LITE_LLM_PROXY_USER_MAX_PARALLEL_REQUESTS=5    # 5 concurrent requests
```

Diese Einstellungen gelten für neue Benutzer, die im System erstellt werden. Bestehende Benutzer behalten ihre konfigurierten Limits.
:::

::: warning Derzeit nicht aktiviert
Obwohl die Infrastruktur diese Limits unterstützt, sind sie standardmässig nicht aktiviert. Setzen Sie die oben genannten Umgebungsvariablen, um Budget- und Ratenbegrenzungen zu aktivieren.
:::

## Optimierungsstrategien

### Modellwahl

Passen Sie die Modellstufe an Ihre Aufgabe an. Verwenden Sie Flagship-Modelle (GPT-5) für komplexe, kundenorientierte oder Aufgaben mit hoher Genauigkeit. Verwenden Sie Balanced-Modelle (GPT-5 mini) für interne Assistenten oder Standard-Workflows. Verwenden Sie effiziente Modelle (GPT-5 nano) für Klassifizierung, Datenextraktion oder hochfrequenten Chat.

### Lokal gehostete Modelle

Lokales Hosting verlagert Ausgaben von variablen Pro-Token-Gebühren auf feste Infrastrukturkosten. Organisationen wählen dies aus Gründen des Datenschutzes (HIPAA, GDPR), der Compliance und des IP-Schutzes, nicht wegen sofortiger Kosteneinsparungen. Es erfordert Kapitalinvestitionen (GPUs, Server) und laufende Betriebskosten (Strom, MLOps-Personal).
