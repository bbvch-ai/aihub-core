---
title: Kostenkontrolle
source_sha: 680b4ecab6faec8d2f79431fd6e748b2f044a6596fb565367e156030495e5de1
---

# Kostenkontrolle

KI-Agents verursachen Betriebskosten. Der Swiss AI Hub verfolgt diese Kosten, damit Sie Ausgaben optimieren,
Investitionen rechtfertigen und Budgets prognostizieren können.

## Wie KI-Kosten funktionieren

KI-Anbieter berechnen Kosten basierend auf der Token-Nutzung. Tokens sind kleine Textabschnitte (ungefähr 4 Zeichen),
die Modelle verarbeiten.

Kostenmodell-Vergleich:

| Modell              | Typ                | Kostenstruktur                                                                                                                                                                     |
| :------------------ | :----------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| API (Pay-per-token) | Variable OPEX      | Bezahlen Sie Anbieter (OpenAI, Google) für jedes verarbeitete Token                                                                                                                |
| Lokal gehostet      | CAPEX + Feste OPEX | Investitionskosten für Hardware (GPUs, Server) plus laufende Kosten für Strom und MLOps-Personal. Die Kosten pro Token betragen \$0, aber die festen Infrastrukturkosten sind hoch |

Jede Interaktion verbraucht verschiedene Arten von Tokens zu unterschiedlichen Preisen:

::: details Prompt-Tokens
Ihre Eingabe an die KI, einschliesslich Fragen, Gesprächsverlauf, System-Prompts und abgerufener Dokumente. Längere
Prompts kosten mehr.
:::

::: details Completion-Tokens
Die von der KI generierten Antworten. Längere, detailliertere Antworten kosten mehr.
:::

::: details Embedding-Tokens
Dokumentenverarbeitung für Suche und Abruf. Typischerweise günstiger als Textgenerierung.
:::

::: details Modellstufen
| Stufe     | Beispiele  | Anwendungsfall                                              | Kosten     |
| :-------- | :--------- | :---------------------------------------------------------- | :--------- |
| Flagship  | GPT-5      | Komplexe Schlussfolgerungen, Aufgaben mit hoher Genauigkeit | Höchste    |
| Balanced  | GPT-5 mini | Standard-Workflows, interne Assistenten                     | Mittel     |
| Efficient | GPT-5 nano | Einfache Aufgaben mit hohem Volumen, Klassifizierung        | Niedrigste |
:::

## Kostenverfolgung

Der Swiss AI Hub verfolgt die Kosten für jede Konversation. Wenn Sie mit einem Agent chatten, zeichnet die Plattform die
Token-Nutzung auf und berechnet die Kosten. Diese Informationen erscheinen im Konversations-Thread.

Die Verfolgung funktioniert für alle KI-Modelle, unabhängig davon, ob Sie Cloud-Services wie OpenAI oder selbst
gehostete Modelle verwenden. Für selbst gehostete Modelle können Sie einen Kostenwert zuweisen, um die Ausgaben
konsistent zu verfolgen.

Sie können Kosteninformationen pro Konversation anzeigen, um zu sehen, welche Fragen am teuersten sind. Dies hilft bei
Agent-Design-Entscheidungen, der Modellwahl und der Budgetplanung.

## Nutzung pro Mandant

Jeder Modellaufruf, den der Swiss AI Hub für einen Benutzer ausführt, wird dem Mandanten zugerechnet, in dem der Benutzer
gerade arbeitet. Das gilt für Chats über OpenWebUI, die OpenAI-kompatible API, Agentenläufe (Chat, Embeddings und
Reranking), Übersetzungen und Spracherkennung. Der LiteLLM-Proxy erfasst den Mandanten als seinen *Kunden* (Customer),
benannt nach dem Mandanten. Gehört ein Benutzer zwei Mandanten an, wird jeder Aufruf nur in dem Mandanten gezählt, in dem
er gerade gearbeitet hat.

Aufrufe ausserhalb eines Mandanten werden dem Kunden `no-tenant` zugerechnet: Sysadmins, die ausserhalb eines Mandanten
arbeiten, geplante Agentenläufe, Datenpipelines, das Schreiben von Erinnerungen und das Parsen von Dokumenten. Sie
erscheinen als eigene Zeile, nie innerhalb eines Mandanten.

Die Kosten werden aus den Preisen berechnet, die in LiteLLM für jedes Modell konfiguriert sind.

### Nutzung eines Mandanten im letzten Monat ablesen

Auf einer gemeinsam genutzten Instanz, die mehrere Mandanten bedient:

1. Öffnen Sie die LiteLLM-Oberfläche unter `https://litellm.<Ihre Domain>/ui` und melden Sie sich als
   Proxy-Administrator an.
2. Öffnen Sie **Usage** und wechseln Sie die Ansicht von **Global Usage** zu **Customer Usage**.
3. Setzen Sie **Select Time Range** auf den ersten und letzten Tag des Monats.
4. Wählen Sie unter **Select customer to filter** den Mandanten anhand seines Namens.
5. Lesen Sie die Zahlen ab:
   - Reiter **Cost**: Gesamtkosten, Anfragen und Tokens des Mandanten sowie die Kosten pro Modell.
   - Reiter **Model Activity**: Anfragen, Tokens und Kosten pro Modell, mit Prompt-Tokens (Eingabe) und
     Completion-Tokens (Ausgabe) getrennt unter **Total Tokens Over Time**.
   - **Export Data** lädt dieselben Zahlen als Datei herunter.

Ohne Kundenfilter listet der Reiter **Cost** unter **Spend Per Customer** jeden Mandanten und `no-tenant` auf. Ihre Summe
entspricht dem Instanz-Total, das **Global Usage** für denselben Zeitraum zeigt.

::: details Die Zahlen über die API ablesen
Die Oberfläche liest sie aus der Admin-API von LiteLLM, die Sie mit dem LiteLLM-Master-Key abfragen können. Die Antwort
listet jeden Tag mit seinen Prompt-Tokens, Completion-Tokens und Kosten, insgesamt und pro Modell:

```bash
curl -s "https://litellm.<your domain>/customer/daily/activity?end_user_ids=<tenant id>&start_date=2026-10-01&end_date=2026-10-31&page_size=1000" \
  -H "Authorization: Bearer $LITELLM_MASTER_KEY"
```

`/customer/list` listet die Kunden mit ihren Mandantennamen, und `/user/daily/activity` mit denselben Daten liefert das
Instanz-Total.
:::

### Nutzung einer dedizierten Instanz im letzten Monat ablesen

Auf einer Instanz, die einen einzigen Kunden bedient, ist die gesamte Instanz die Nutzung dieses Kunden. Öffnen Sie
**Usage** → **Global Usage**, setzen Sie den Zeitraum auf den Monat und lesen Sie die Totale und den Reiter **Model
Activity** wie oben ab.

::: warning Aufrufe, bevor Mandanten erfasst wurden
Nur Aufrufe, seit der Swiss AI Hub Mandanten erfasst, werden einem Mandanten zugerechnet. Frühere Aufrufe über die
OpenAI-kompatible API erscheinen unter Kunden, die nach einer Benutzer-ID benannt sind, und frühere Aufrufe ohne Benutzer
unter gar keinem Kunden. Deployments mit eigener LiteLLM-Konfiguration müssen den Callback `tenant_attribution`
registrieren, der neben `custom_callbacks.py` ausgeliefert wird, sonst fehlen Aufrufe ohne Mandanten in der
Kundenansicht.
:::

## Budgets und Ratenbegrenzungen

LiteLLM bietet pro Benutzer Budget- und Ratenbegrenzungsfunktionen über sein Benutzerverwaltungssystem. Diese Kontrollen
werden über Umgebungsvariablen konfiguriert und automatisch vom Proxy durchgesetzt.

Verfügbare Kontrollen:

- Max. Budget: Harte Obergrenze für Ausgaben pro Benutzer innerhalb eines Budgetzeitraums. Blockiert Anfragen bei
  Überschreitung.

- Soft Budget: Warnschwelle, die Benachrichtigungen auslöst, ohne Anfragen zu blockieren.

- Budgetdauer: Zeitraum für die Budgetrücksetzung (z.B. "30d" für monatliche Budgets). Ohne diese werden Budgets nie
  zurückgesetzt.

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

Diese Einstellungen gelten für neue Benutzer, die im System erstellt werden. Bestehende Benutzer behalten ihre
konfigurierten Limits.
:::

::: warning Derzeit nicht aktiviert
Obwohl die Infrastruktur diese Limits unterstützt, sind sie standardmässig nicht aktiviert. Setzen Sie die oben
genannten Umgebungsvariablen, um Budget- und Ratenbegrenzungen zu aktivieren.
:::

## Optimierungsstrategien

### Modellwahl

Passen Sie die Modellstufe an Ihre Aufgabe an. Verwenden Sie Flagship-Modelle (GPT-5) für komplexe, kundenorientierte
oder Aufgaben mit hoher Genauigkeit. Verwenden Sie Balanced-Modelle (GPT-5 mini) für interne Assistenten oder
Standard-Workflows. Verwenden Sie effiziente Modelle (GPT-5 nano) für Klassifizierung, Datenextraktion oder
hochfrequenten Chat.

### Lokal gehostete Modelle

Lokales Hosting verlagert Ausgaben von variablen Pro-Token-Gebühren auf feste Infrastrukturkosten. Organisationen wählen
dies aus Gründen des Datenschutzes (HIPAA, GDPR), der Compliance und des IP-Schutzes, nicht wegen sofortiger
Kosteneinsparungen. Es erfordert Kapitalinvestitionen (GPUs, Server) und laufende Betriebskosten (Strom,
MLOps-Personal).
