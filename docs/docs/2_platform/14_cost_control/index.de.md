---
title: Kostenkontrolle
source_sha: adc3a71968238d27faaa572662887d4b5f3f0a00356138445a61f32d99a4fb04
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
| Lokal gehostet      | CAPEX + Feste OPEX | Investitionskosten für Hardware (GPUs, Server) plus laufende Kosten für Strom und MLOps-Personal. Die Kosten pro Token betragen 0, aber die festen Infrastrukturkosten sind hoch |

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

## Wie Kosten berechnet werden

Jeder Betrag, den die Plattform ausweist, ist eine Token-Anzahl oder eine Dauer, multipliziert mit einem Preis aus der
LiteLLM-Konfiguration. Ein Preis wird nirgends sonst nachgeschlagen: Ein Modell ohne konfigurierten Preis kostet 0.

### Währung

Alle Preise und Kosten sind in **CHF** angegeben, der Währung, in der die Provider abrechnen. Das gilt für die Kosten
pro Konversation, die Admin UI, die Hub API, die Usage-Ansichten von LiteLLM, Langfuse und Benutzerbudgets.

::: warning Das Dollarzeichen in LiteLLM und Langfuse
LiteLLM und Langfuse haben keine Währungseinstellung und zeigen immer „\$" an. Die angezeigten Beträge sind CHF.
:::

### Woher die Preise stammen

Preise werden pro Modell in der LiteLLM-Konfiguration festgelegt, als Preis pro Token (`input_cost_per_token`,
`output_cost_per_token`) oder pro Sekunde Audio (`input_cost_per_second`). Jeder Preis wird aus der CHF-Preisliste des
Providers übernommen oder, wenn ein Provider keine veröffentlicht, aus seinem Nutzungsbericht ermittelt.

Die Docker-Compose-Deployments beziehen ihre Preise aus `infra/deployment/compose-config.yml`; die Dateien in
`infra/configs/litellm/` werden daraus generiert. Kubernetes-Deployments führen ihre eigenen Preise in der
LiteLLM-Konfiguration ihres Charts, nach denselben Regeln.

### Wie jeder Aufruf bepreist wird

LiteLLM bucht die Kosten jedes Aufrufs in seinem Spend Log, auf Basis der Usage, die der Provider zurückgibt:

| Aufruf                       | Gebuchte Kosten                                                                                           |
| ---------------------------- | --------------------------------------------------------------------------------------------------------- |
| Chat                         | Prompt-Tokens × Eingabepreis + Completion-Tokens × Ausgabepreis                                           |
| Chat mit Reasoning           | Reasoning-Tokens gehören zu den Completion-Tokens und kosten den Ausgabepreis                             |
| Chat mit gecachter Eingabe   | Gecachte Prompt-Tokens kosten den vollen Eingabepreis; ein reduzierter Cache-Preis ist nicht konfiguriert |
| Gestreamter Chat             | Gleich wie ohne Streaming; LiteLLM fordert beim Provider immer die Usage an                               |
| Embedding                    | Eingabe-Tokens × Eingabepreis                                                                             |
| Rerank                       | Eingabe-Tokens × Eingabepreis; die Usage-Ansichten zeigen die Kosten, aber 0 Tokens                       |
| Transkription                | Sekunden Audio, wie vom Provider gemeldet, × Preis pro Sekunde; 0 Tokens                                  |
| Fallback                     | Der Preis des Modells, das geantwortet hat, gebucht unter dem Namen dieses Modells                        |
| Cache-Treffer                | 0, da der Provider nicht aufgerufen wird; die Tokens werden erneut gezählt                                |
| Modell ohne Preis            | 0; die Tokens werden trotzdem erfasst                                                                     |
| Provider liefert keine Usage | 0 Tokens und 0 Kosten ohne Streaming; mit Streaming zählt LiteLLM die Tokens selbst                       |

Die Konfigurationen cachen Embeddings für einen Tag, sodass wiederholte Embeddings desselben Texts kostenlos sind, aber
erneut in den Token-Summen erscheinen. Ein Aufruf eines Modells, der fehlschlägt, fällt auf
`text-generation/gemma-4-31B-it` zurück und wird zu dessen Preis gebucht.

### Drei Beträge für dieselben Aufrufe

| Betrag            | Wo er angezeigt wird                          | Tokens gezählt aus                                                                                                                         |
| ----------------- | --------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| LiteLLM Spend Log | Usage- und Customer-Usage-Ansicht von LiteLLM | Der Usage, die der Provider zurückgibt                                                                                                     |
| Hub-Kostenevents  | Kosten pro Konversation, Admin UI             | Der Usage, die der Provider zurückgibt, oder einem lokalen Tokenizer, wenn keine vorhanden ist; bei Embeddings immer dem lokalen Tokenizer |
| Langfuse          | Traces                                        | Der Usage im Trace, bepreist über Modelldefinitionen, die aus den Preisen von LiteLLM erstellt wurden                                      |

Der LiteLLM Spend Log ist der Betrag, der mit Rechnungen verglichen werden sollte: Er umfasst jeden Aufruf über den
Proxy. Hub-Kostenevents umfassen nur Agent-Runs. Langfuse bepreist jeden Trace zu dem Preis, der galt, als der Trace
entstand: Die Hub API legt bei jedem Start, an dem sie einen geänderten Preis findet, eine Definition mit dem neuen Preis
an, die ab diesem Zeitpunkt gilt. Modelle, die pro Sekunde Audio bepreist werden, etwa Transkription, werden in Langfuse
nicht bepreist.

### Preise der Docker-Compose-Deployments

Am 2026-11-17 mit den Preislisten der Provider abgeglichen. Preise pro Million Tokens, sofern nicht anders angegeben.

| Modell                                          | Provider         | Eingabe            | Ausgabe | Quelle und Prüfung                                                                 |
| ----------------------------------------------- | ---------------- | ------------------ | ------- | ---------------------------------------------------------------------------------- |
| `text-generation/gemma-4-31B-it`                | Infomaniak       | 0.20               | 0.40    | Preisseite von Infomaniak; stimmt überein                                          |
| `text-generation/gemma-4-31B-it` (stoney)       | stoney           | 0.25               | 1.00    | Aus dem Nutzungsbericht von stoney ermittelt, der keine öffentliche Preisliste hat |
| `text-generation/Ministral-3-14B-Instruct-2512` | Infomaniak       | 0.30               | 0.40    | Preisseite von Infomaniak; stimmt überein                                          |
| `text-generation/Kimi-K2.6`                     | Infomaniak       | 0.60               | 3.00    | Preisseite von Infomaniak; stimmt überein                                          |
| `text-generation/Apertus-70B-Instruct-2509`     | Infomaniak       | 0.70               | 2.50    | Die Preisseite führt nur Apertus-v1.5-70B, zu diesem Preis                         |
| `text-generation/Qwen3.5-122B-A10B-FP8`         | Infomaniak       | 0.40               | 3.20    | Nicht mehr auf der Preisseite; nicht verifiziert                                   |
| `embedding/bge-m3`                              | Phoeniqs         | 0.4309             | -       | Phoeniqs veröffentlicht keine Preisliste; nicht verifiziert                        |
| `reranker/bge`                                  | Phoeniqs         | 0.0077             | -       | Phoeniqs veröffentlicht keine Preisliste; nicht verifiziert                        |
| `transcription/whisper-large-v3`                | Phoeniqs         | 0.00245 pro Minute | -       | Phoeniqs veröffentlicht keine Preisliste; nicht verifiziert                        |
| `text-generation/MinerU2.5-2509-1.2B` (OCR)     | stoney           | ohne Preis         |         | stoney veröffentlicht keinen Preis; kostet 0                                       |
| `image-generation/flux`                         | nicht festgelegt | ohne Preis         |         | Standardmässig ist kein Provider konfiguriert; kostet 0                            |
| Alle Modelle der `*.gpu`-Varianten              | Eigene GPUs      | 0                  | 0       | Bewusst mit 0 bepreist: Die Kosten liegen in der Hardware, nicht im Aufruf         |

### Preise aktuell halten

Wenn ein Provider einen Preis ändert oder ein Modell hinzukommt:

1. Übernehmen Sie den CHF-Preis aus der Preisliste des Providers oder ermitteln Sie ihn aus seinem Nutzungsbericht.
2. Tragen Sie ihn als Preis pro Token (pro Million geteilt durch 1'000'000) in `infra/deployment/compose-config.yml` und
   in der LiteLLM-Konfiguration des Kubernetes-Charts ein, mit einem Kommentar, der Quelle und Datum nennt.
3. Führen Sie `make generate-compose` aus und aktualisieren Sie die obige Tabelle.

Für einen Provider, der in einer anderen Währung abrechnet, muss der Preis bei der Erfassung in CHF umgerechnet werden,
mit Kurs und dessen Datum im Kommentar.

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
LITE_LLM_PROXY_USER_MAX_BUDGET=100.0           # 100 CHF hard limit
LITE_LLM_PROXY_USER_SOFT_BUDGET=80.0           # Alert at 80 CHF
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
