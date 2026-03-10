---
title: Kostenkontrolle
source_sha: 65d64babdb0d0f2b37dcc4c2a7a166007db5749a1f505f9ce2df3ed1910496f8
---

# Kostenkontrolle

KI-Agenten verursachen Betriebskosten. Der Swiss AI Hub verfolgt diese Kosten, damit Sie Ausgaben optimieren,
Investitionen rechtfertigen und Budgets prognostizieren können.

## Wie KI-Kosten funktionieren

KI-Anbieter berechnen Kosten basierend auf der Token-Nutzung. Tokens sind kleine Textabschnitte (ungefähr 4 Zeichen),
die Modelle verarbeiten.

Vergleich der Kostenmodelle:

| Modell              | Typ                | Kostenstruktur                                                                                                                                                                         |
| ------------------- | ------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| API (Pay-per-Token) | Variable OPEX      | Bezahlen Sie Anbieter (OpenAI, Google) für jedes verarbeitete Token                                                                                                                    |
| Lokal gehostet      | CAPEX + Feste OPEX | Investitionskosten für Hardware (GPUs, Server) plus laufende Kosten für Strom und MLOps-Mitarbeiter. Die Kosten pro Token betragen 0 \$, aber die festen Infrastrukturkosten sind hoch |

Jede Interaktion verbraucht verschiedene Arten von Tokens zu unterschiedlichen Preispunkten:

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

::: details Modellstufen
| Stufe       | Beispiele  | Anwendungsfall                                        | Kosten    |
| ----------- | ---------- | ----------------------------------------------------- | --------- |
| Flaggschiff | GPT-5      | Komplexe Denkprozesse, Aufgaben mit hoher Genauigkeit | Höchste   |
| Ausgewogen  | GPT-5 mini | Standard-Workflows, interne Assistenten               | Mittel    |
| Effizient   | GPT-5 nano | Einfache Aufgaben mit hohem Volumen, Klassifizierung  | Geringste |
:::

## Kostenverfolgung

Der Swiss AI Hub verfolgt die Kosten für jede Konversation. Wenn Sie mit einem Agenten chatten, zeichnet die Plattform
die Token-Nutzung auf und berechnet die Kosten. Diese Informationen erscheinen im Konversations-Thread.

Die Verfolgung funktioniert für alle KI-Modelle, egal ob Sie Cloud-Dienste wie OpenAI oder selbst gehostete Modelle
verwenden. Für selbst gehostete Modelle können Sie einen Kostenwert zuweisen, um die Ausgaben konsistent zu verfolgen.

Sie können Kosteninformationen pro Konversation anzeigen, um zu sehen, welche Fragen am teuersten sind. Dies hilft bei
Entscheidungen zum Agenten-Design, der Modellauswahl und der Budgetplanung.

## Budgets und Ratenbegrenzungen

LiteLLM bietet pro-Benutzer-Budget- und Ratenbegrenzungsfunktionen über sein Benutzerverwaltungssystem. Diese Kontrollen
werden über Umgebungsvariablen konfiguriert und automatisch vom Proxy durchgesetzt.

Verfügbare Kontrollen:

- Maximales Budget: Eine harte Obergrenze für die Ausgaben pro Benutzer innerhalb einer Budgetperiode. Blockiert
  Anfragen bei Überschreitung.

- Soft Budget: Eine Warnschwelle, die Benachrichtigungen auslöst, ohne Anfragen zu blockieren.

- Budgetdauer: Der Zeitraum für die Budget-Zurücksetzung (z.B. „30d“ für monatliche Budgets). Ohne diese werden Budgets
  nie zurückgesetzt.

- TPM-Grenze: Maximale Tokens pro Minute, die ein Benutzer verbrauchen kann.

- RPM-Grenze: Maximale Anfragen pro Minute, die ein Benutzer stellen kann.

- Maximale parallele Anfragen: Maximale gleichzeitige Anfragen, die ein Benutzer offen haben kann.

::: details Konfiguration über Umgebungsvariablen
```bash
LITE_LLM_PROXY_USER_MAX_BUDGET=100.0           # $100 hard limit
LITE_LLM_PROXY_USER_SOFT_BUDGET=80.0           # Alert at $80
LITE_LLM_PROXY_USER_BUDGET_DURATION="30d"      # Reset monthly
LITE_LLM_PROXY_USER_TPM_LIMIT=10000            # 10k tokens/minute
LITE_LLM_PROXY_USER_RPM_LIMIT=60               # 60 requests/minute
LITE_LLM_PROXY_USER_MAX_PARALLEL_REQUESTS=5    # 5 concurrent requests
```

Diese Einstellungen gelten für neue Benutzer, die im System erstellt werden. Bestehende Benutzer behalten ihre
konfigurierten Limits bei.
:::

::: warning Derzeit nicht aktiviert
Obwohl die Infrastruktur diese Limits unterstützt, sind sie standardmäßig nicht aktiviert. Setzen Sie die oben genannten
Umgebungsvariablen, um Budget- und Ratenbegrenzungen zu aktivieren.
:::

## Optimierungsstrategien

### Modellauswahl

Passen Sie die Modellstufe Ihrer Aufgabe an. Verwenden Sie Flaggschiff-Modelle (GPT-5) für komplexe, kundenorientierte
oder hochpräzise Aufgaben. Verwenden Sie ausgewogene Modelle (GPT-5 mini) für interne Assistenten oder
Standard-Workflows. Verwenden Sie effiziente Modelle (GPT-5 nano) für Klassifizierung, Datenextraktion oder häufige
Chats.

### Lokal gehostete Modelle

Lokales Hosting verlagert Ausgaben von variablen Pay-per-Token-Gebühren auf feste Infrastrukturkosten. Organisationen
wählen dies aus Gründen des Datenschutzes (HIPAA, GDPR), der Compliance und des IP-Schutzes, nicht wegen sofortiger
Kosteneinsparungen. Es erfordert Kapitalinvestitionen (GPUs, Server) und laufende Betriebskosten (Strom,
MLOps-Personal).
