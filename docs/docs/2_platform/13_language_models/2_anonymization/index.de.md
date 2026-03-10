---
title: Datenanonymisierung
source_sha: 04c5b6fd0bcecec3e53c487698ab5b03f9581785569786af4c40469a15eefc39
---

# Datenanonymisierung

Der Swiss AI Hub integriert Presidio zur Erkennung und Anonymisierung von persönlich identifizierbaren Informationen
(PII) in Benutzeranfragen, bevor diese externe LLM-Anbieter erreichen.

## Was Presidio schützt

Presidio erfasst PII, die Benutzer versehentlich in ihre Fragen aufnehmen:

- „Können Sie diesen Vertrag für John Smith (john.smith@company.com) überprüfen?“
- „Wie lautet die Richtlinie für die Kreditkarte 4532-1234-5678-9012?“
- „Wie bearbeite ich die Rechnung für die Telefonnummer +41 79 123 45 67?“

Ohne Presidio werden diese PII als Teil der API-Anfrage an externe LLM-Anbieter (OpenAI, Google) gesendet.

## Wie es funktioniert

Presidio läuft als Schutzmechanismus (Guardrail) in der LiteLLM-Proxy-Schicht. Es scannt Benutzerfragen nach
PII-Mustern, bevor Anfragen an Sprachmodelle gesendet werden.

Zwei Anonymisierungsmodi:

Der Maskierungsmodus (Mask mode) ersetzt erkannte PII durch Platzhalter wie `[PERSON]` oder `[EMAIL_ADDRESS]`. Die Frage
„Können Sie diesen Vertrag für John Smith überprüfen?“ wird zu „Können Sie diesen Vertrag für [PERSON] überprüfen?“,
bevor sie das LLM erreicht. Das Modell kann den Kontext weiterhin verstehen und eine nützliche Antwort generieren.

Der Blockierungsmodus (Block mode) lehnt die gesamte Anfrage ab, wenn bestimmte PII-Typen auftreten. Verwenden Sie
diesen Modus für hochsensible Daten wie Kreditkartennummern. Der Benutzer erhält eine Fehlermeldung anstelle einer
Antwort.

## Unterstützte PII-Typen

Presidio erkennt Personennamen, E-Mail-Adressen, Kreditkartennummern, Telefonnummern, Sozialversicherungsnummern,
IP-Adressen sowie Daten oder Orte, die Personen identifizieren könnten. Die Erkennung erfolgt mittels Musterabgleich,
regulären Ausdrücken und Modellen zur Erkennung benannter Entitäten (Named Entity Recognition). Das System unterstützt
mehrere Sprachen, darunter Englisch, Deutsch, Französisch und Italienisch.

## Konfiguration

Presidio-Guardrails werden in LiteLLM konfiguriert, sind aber standardmäßig deaktiviert. Administratoren aktivieren sie
pro Deployment basierend auf den Anforderungen an die Datensensitivität.

::: details Beispielkonfiguration für Guardrails:
```yaml
guardrails:
  - guardrail_name: "presidio-mask-guard"
    litellm_params:
      guardrail: presidio
      default_on: false
      mode: "pre_call"
      presidio_language: "de"
      output_parse_pii: true
      pii_entities_config:
        PERSON: "MASK"
        EMAIL_ADDRESS: "MASK"

  - guardrail_name: "presidio-block-guard"
    litellm_params:
      guardrail: presidio
      default_on: false
      mode: "pre_call"
      pii_entities_config:
        CREDIT_CARD: "BLOCK"
```

Konfigurieren Sie, welche PII-Typen maskiert oder blockiert werden sollen, über den Abschnitt `pii_entities_config`.
Setzen Sie `default_on: true`, um den Guardrail für alle Anfragen zu aktivieren.
:::

## Wann Anonymisierung eingesetzt werden sollte

| Szenario                                    | Empfehlung                                                                            |
| ------------------------------------------- | ------------------------------------------------------------------------------------- |
| Externe LLM-Anbieter (OpenAI, Google usw.)  | Aktivieren Sie Presidio, um Daten zu schützen, bevor sie Ihre Infrastruktur verlassen |
| Selbst gehostete Modelle On-Premises        | Optional – Ihre Daten verlassen niemals Ihre Kontrolle                                |
| Von Benutzern generierte Inhalte            | Aktivieren Sie, wenn Benutzer versehentlich PII einschließen könnten                  |
| Vorbereinigte Daten                         | Überspringen Sie Presidio, um unnötigen Overhead zu vermeiden                         |
| Regulatorische Anforderungen (DSGVO, HIPAA) | Aktivieren Sie, um PII-Schutzkontrollen zu demonstrieren                              |

Presidio wird auf alle Anfragen angewendet, wenn es aktiviert ist. Verwenden Sie den Blockierungsmodus sparsam – nur für
hochsensible PII-Typen wie Kreditkarten, bei denen eine strikte Ablehnung anstelle einer Maskierung erforderlich ist.
