---
title: Datenanonymisierung
source_sha: 5c0f6cb342daadcee64f8580f7a698776141658fa18c494dad63d1c22732f2e1
---

# Datenanonymisierung

Der Swiss AI Hub kann Personendaten in Anfragen an Sprachmodelle durch Platzhalter ersetzen und die ursprünglichen Werte
in die Antwort einsetzen, bevor der Benutzer sie sieht. Das Modell sieht nie einen Namen, eine Adresse oder eine
AHV-Nummer; der Benutzer liest eine normale Antwort. Ein Deployment schaltet es für jedes ausserhalb gehostete Modell
ein, ein Agentenprofil für seine eigenen Aufrufe.

## Was Benutzer sehen

Ein Benutzer fragt: «Entwirf eine Mahnung für Reto Wyss, AHV 756.1234.5678.97, Seefeldstrasse 18, 8008 Zürich.»

- Das externe Modell erhält: «Entwirf eine Mahnung für `<PERSON_1>`, AHV `<NATIONAL_ID_2>`, `<CH_ADDRESS_3>`.»
- Das Modell antwortet mit den Platzhaltern, zum Beispiel «Sehr geehrter `<PERSON_1>`, …».
- Der Benutzer liest «Sehr geehrter Reto Wyss, …», Wort für Wort, während die Antwort gestreamt wird.

Derselbe Wert behält innerhalb einer Anfrage denselben Platzhalter, sodass das Modell Personen weiterhin unterscheiden
kann. Platzhalter, die bereits in einer Frage stehen (von Hand anonymisierter Text), bleiben unverändert und werden nie
für einen anderen Wert wiederverwendet.

## Funktionsweise

Ein Guardrail im LiteLLM-Gateway (`pii-anonymisation`) verarbeitet jede Chat-Anfrage:

1. Jeder Text der Konversation (System-Prompt, Fragen, frühere Antworten, Tool-Ergebnisse, RAG-Kontext) geht an den
   selbst gehosteten Presidio Analyzer, der die Personendaten findet. Dafür verlässt kein Text das Deployment.
2. Jeder Wert wird durch einen nummerierten Platzhalter ersetzt. Überlappende Erkennungen werden zuerst zusammengeführt,
   sodass ein Platzhalter nie zerbricht.
3. Die Antwort wird beim Eintreffen wiederhergestellt: im Text, im Reasoning des Modells und in Tool-Call-Argumenten
   (die gültiges JSON bleiben). Beim Streaming wird nur ein möglicher Platzhalter-Anfang von wenigen Zeichen
   zurückgehalten.

Ist der Analyzer nicht erreichbar, wird die Anfrage mit einer Fehlermeldung abgelehnt, statt unmaskiert gesendet.

## Welche Aufrufe anonymisiert werden

Drei Schalter entscheiden, und jeder einzelne genügt:

| Schalter                                                 | Wer setzt ihn                                      | Was er anonymisiert                                                                                                                                               |
| -------------------------------------------------------- | -------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `PII_ANONYMISE_EXTERNAL_MODELS=true`                     | Der Betreiber, pro Deployment (standardmässig aus) | Jeden Aufruf an ein ausserhalb des Deployments gehostetes Modell, für jeden Aufrufer: Chats, Agenten (inklusive Titel, Follow-ups und Memory-Extraktion) und Bots |
| **Personendaten anonymisieren** in einem Agentenprofil   | Der Admin des Profils                              | Jeden Aufruf der Läufe dieses Profils, unabhängig vom Modell                                                                                                      |
| Der [Anonymisierer](../../5_agents/14_anonymiser/)-Agent | Jeder Benutzer, von Hand                           | Den Text, den der Benutzer ihm sendet                                                                                                                             |

Jedes Modell in der Gateway-Konfiguration gibt an, wo es läuft (`model_info.aihub_hosting_location`); jedes Modell, das
nicht `local` ist (die Schweizer Cloud-Anbieter und jeder andere externe Anbieter), gilt als ausserhalb des Deployments.
Schalten Sie den Deployment-Schalter ein, wenn externe Modelle Personendaten erhalten könnten, die die Organisation
nicht verlassen dürfen. Ist er aus, senden Chats mit einem externen Modell ihren Text unverändert, und nur Profile mit
der Checkbox anonymisieren. Der Schalter wird beim Start des Gateways gelesen: Umgebungsvariable ändern und `litellm`
neu starten. Ein anderer Wert als `true` oder `false` gilt als `true`, und das Gateway protokolliert einen Fehler.

Ein Aufruf kann den Guardrail auch selbst verlangen:

```json
{"model": "text-generation/Qwen3-VL-30B-A3B-Instruct-FP8", "guardrails": ["pii-anonymisation"], "messages": []}
```

Nur Chat-Anfragen werden anonymisiert. Embeddings, Reranking, Transkription und Bildgenerierung nicht.

::: warning Antworten können schlechter werden
Das Modell arbeitet mit Platzhaltern, nicht mit Werten. Es erkennt nicht, dass zwei Schreibweisen desselben Werts
zusammengehören («Herr Meier» in der Frage, «Hans-Peter Meier» in einem Dokument, oder «Genf» und «Genève» erhalten
verschiedene Platzhalter), kann aus einem maskierten Geburtsdatum kein Alter berechnen und nutzt sein Wissen über eine
maskierte Stadt nicht. Wissensagenten antworten dann, die Dokumente enthielten keine Antwort. Anonymisieren Sie dort, wo
die Daten es verlangen, nicht standardmässig.
:::

### Ein Agentenprofil anonymisieren

Jedes Agentenprofil hat am Ende seines Konfigurationsformulars die Checkbox **Personendaten anonymisieren**, unabhängig
vom Blueprint. Ist sie aktiv, verlangt jeder LLM-Aufruf der Läufe des Profils den Guardrail, auch für Modelle innerhalb
des Deployments: die Antwort, die Meta-Fragen-Prüfung, der Titel, die Follow-ups, die Memory-Extraktion und die Läufe,
an die das Profil delegiert. Die Antwort beginnt mit einem kurzen Hinweis, dass Personendaten ersetzt wurden, bevor sie
das Modell erreichten. Gedacht für Profile mit sensiblen Daten, etwa im HR, auch wenn ihre Modelle on-premises laufen.

### Text von Hand anonymisieren

Benutzer können einen Text auch selbst mit dem Agenten [Anonymisierer](../../5_agents/16_anonymiser/) anonymisieren und
ihn dann in jedem Werkzeug verwenden, innerhalb oder ausserhalb des Hubs. Die Antwort fügen sie in denselben Chat ein
und erhalten sie mit den Originalwerten zurück. Der Anonymisierer verwendet denselben Analyzer und dieselbe Liste
dessen, was als Personendaten gilt, und ruft kein Modell auf.

## Was erkannt wird

Der Analyzer verwendet Presidio mit dem mehrsprachigen PII-Modell von GLiNER und Mustern für Schweizer und
internationale Formate, auf Deutsch, Französisch, Italienisch und Englisch:

| Typ                                   | Beispiele                                                                                                      |
| ------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| Personennamen, Adressen, Orte         | Reto Wyss, «Name: Brunner», «Frau Gerber», Seefeldstrasse 18, 8008 Zürich                                      |
| E-Mail-Adressen, Telefonnummern, IBAN | +41 44 270 41 87, CH93 0076 2011 6238 5295 7                                                                   |
| Nationale Identifikatoren             | AHV-Nummern; US-SSN, UK National Insurance, französische NIR, italienischer Codice fiscale, deutsche Steuer-ID |
| Gesundheitsdaten-Identifikatoren      | Patienten- und Fallnummern, Versichertenkartennummern                                                          |
| Ausweise und Daten                    | Pass- und Identitätskartennummern, Geburtsdaten                                                                |

Andere Daten, Firmennamen und Beschreibungen, die eine Person nur über den Kontext identifizieren (eine Funktion
zusammen mit einer Firma), werden nicht maskiert.

Pronomen, Rollen, Anreden, Feld- und Zimmerbezeichnungen («Sie», «vous», «Benutzer», «Patientin», «Grüezi», «Adresse»,
«IBAN», «Zimmer») werden in Deutsch, Französisch, Italienisch und Englisch nie maskiert, auch mit einer kurzen Nummer
(«Position 2», «Art. 5», «Zimmer 12»): Das Erkennungsmodell hält sie für Namen oder für den Typ, den sie benennen, und
ihre Maskierung würde die Anfrage verfälschen. Die Liste ist `pii_allow_list` in der Gateway-Konfiguration.

## Prüfen in Langfuse

Jeder Aufruf, den das Gateway anonymisiert, hinterlässt in Langfuse eine Observation `pii-anonymisation`. In einem
Agentenlauf steht sie im Trace des Laufs, neben dem Schritt, der den Aufruf gemacht hat: Ihr Input ist die Anfrage genau
so, wie der Anbieter sie erhalten hat, mit Platzhaltern, ihr Output nennt, wie viele Werte welchen Typs ersetzt wurden,
und ihre Metadaten nennen das Modell und den Grund der Anonymisierung (ein Modell ausserhalb des Deployments oder vom
Aufruf verlangt, etwa durch die Checkbox eines Profils). Alle anonymisierten Aufrufe zeigt Tracing → Observations mit
der Suche nach `pii-anonymisation`. Aufrufe ausserhalb eines Agentenlaufs, etwa einfache Chats, erscheinen nur mit ihren
Zählungen. Ein abgelehnter Aufruf, weil der Analyzer nicht erreichbar war, erscheint als Fehler.

Die übrigen Observations eines Laufs zeichnet der Agent auf, bevor der Aufruf das Gateway erreicht; sie zeigen deshalb
den Originaltext. Langfuse läuft innerhalb des Deployments.

## Konfiguration

::: details Gateway-Konfiguration (generiert aus `litellm-config.yml.j2`):
```yaml
guardrails:
  - guardrail_name: "pii-anonymisation"
    litellm_params:
      guardrail: pii_anonymisation_guardrail.PiiAnonymisationGuardrail
      mode: [pre_call, post_call]
      default_on: false   # der Guardrail läuft selbst bei jedem Modell, das nicht `local` ist
      presidio_language: "de"
      pii_entities_config:
        PERSON: "MASK"
        CH_ADDRESS: "MASK"
        NATIONAL_ID: "MASK"
        # ... die vollständige Liste steht im Template
      pii_allow_list: [sie, ihnen, Benutzer, Adresse, IBAN]   # nie maskiert; vollständige Liste im Template

model_list:
  - model_name: text-generation/gemma-4-31B-it
    model_info:
      aihub_hosting_location: swiss_cloud   # local | swiss_cloud | eu | global
```

URL und Schlüssel des Analyzers kommen aus `PRESIDIO_ANALYZER_API_BASE` und `PRESIDIO_ANALYZER_API_KEY`. Die Recognizer
stehen in `infra/deployment/templates/configs/presidio-analyzer.yaml`; Änderungen brauchen `make generate-compose` und
einen Neustart des Analyzers, keinen Image-Build.
:::

## Grenzen

- Das Modell muss Platzhalter genau so zurückschreiben, wie es sie erhalten hat. Ein Modell, das sie verändert
  (`<Person_1>`), lässt sie in der Antwort stehen.
- Die Analyse verlängert jede Anfrage: um einige hundert Millisekunden bei einer Frage, um etwa 50 Sekunden auf der CPU
  bei einem Prompt mit 20'000 Tokens wie einem langen Mail-Verlauf.
- Die Muster für Fallnummern, Versichertenkarten, Ausweise und Geburtsdaten wurden anhand synthetischer Testdaten
  geschrieben; prüfen Sie sie an Ihren eigenen Dokumentformaten.
