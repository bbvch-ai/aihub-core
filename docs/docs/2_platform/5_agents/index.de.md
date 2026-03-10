---
title: Agenten
source_sha: c4eeca3ff84082a35213e53a1a68470b5b1f85240ecb0c4e2bf9e0cb9e7708d2
---

# Agenten

Agenten sind spezialisierte KI-Assistenten, die bestimmte Aufgaben durch strukturierte Workflows ausführen. Im Gegensatz
zu offenen Chatbots folgen Agenten vordefinierten Schritten, um Dokumente zu analysieren, Fragen zu beantworten oder
Geschäftsprozesse abzuschließen.

Agenten können interaktiv sein (auf Benutzerfragen per Chat antworten) oder autonom (Aufgaben automatisch nach einem
Zeitplan oder durch Ereignisse ausgelöst ausführen). Der strukturierte Workflow-Ansatz macht Agenten vorhersehbar,
transparent und überprüfbar, unabhängig davon, wie sie arbeiten.

## Was ist ein Agent?

Ein Agent ist ein KI-gestützter Assistent, der für die Bearbeitung spezifischer Aufgaben unter Verwendung eines
vordefinierten Workflows konfiguriert ist.

Beispiele:

- Ein HR-Richtlinien-Agent beantwortet Mitarbeiterfragen zu Urlaubsrichtlinien, indem er das Mitarbeiterhandbuch
  konsultiert (interaktiv, Chat-basiert).
- Ein Compliance-Monitoring-Agent überprüft Dokumente nach einem Zeitplan und kennzeichnet potenzielle
  Richtlinienverstöße (autonom, zeitgesteuert).

Agenten kombinieren große Sprachmodelle (LLMs) zum Verständnis natürlicher Sprache mit strukturierten Prozessen für
einen zuverlässigen Betrieb.

## Agenten-"Training"

Eine häufige Frage ist, ob Agenten mit Unternehmensdaten „trainiert“ werden können. Der Swiss AI Hub bietet kein
Modelltraining oder Fine-Tuning an. Stattdessen greifen Agenten über ihre Wissensdatenbanken auf aktuelle Informationen
zu.

Wenn Personen nach dem Training eines Agenten fragen, möchten sie in der Regel, dass der Agent die spezifischen
Informationen ihres Unternehmens kennt. Die Plattform erreicht dies durch Retrieval-Augmented Generation (RAG). Der
Agent ruft relevante Informationen aus Ihrer Wissensdatenbank ab, wenn er Fragen beantwortet, anstatt diese
Informationen direkt im Modell eingebettet zu haben.

Vorteile dieses Ansatzes:

- Informationen bleiben aktuell. Aktualisieren Sie Ihre Dokumente, und Agenten verwenden die neuen Informationen sofort
  ohne erneute Verarbeitung.
- Transparenz. Sie können genau sehen, welche Dokumente der Agent zur Beantwortung jeder Frage herangezogen hat.
- Flexibilität. Verschiedene Agenten können auf verschiedene Teilsätze Ihrer Wissensdatenbank zugreifen, indem Sie
  konfigurieren, welche Sammlungen sie durchsuchen dürfen.

Agenten „lernen“, indem sie auf eine aktuelle Wissensdatenbank zugreifen, die über Datenpipelines gepflegt wird. Fügen
Sie neue Dokumente hinzu oder aktualisieren Sie bestehende, und Agenten integrieren diese Informationen automatisch.

## Wie Agenten funktionieren

Das Verhalten eines Agenten folgt einem Workflow, einer vordefinierten Abfolge von Schritten. Dies unterscheidet sich
von allgemeiner konversationeller KI.

Beispiel-Workflow für einen Frage-Antwort-Agenten:

1. Anfrage verstehen: Der Agent verwendet ein LLM, um Ihre Frage zu interpretieren.
2. Informationen abrufen: Der Agent durchsucht eine zugewiesene Wissensdatenbank (z. B. einen SharePoint-Ordner) nach
   relevanten Dokumenten mittels semantischer Suche (RAG).
3. Antwort synthetisieren: Der Agent kombiniert Ihre Frage mit abgerufenen Informationen und generiert eine Antwort.
4. Quellen zitieren: Die Antwort enthält Verweise auf Quelldokumente zur Überprüfung.

Vorteile des Workflows:

- Transparenz: Sie können sehen, welche Dokumente der Agent konsultiert hat.
- Zuverlässigkeit: Die Beschränkung des Agenten auf einen Workflow und eine Wissensdatenbank reduziert Halluzinationen
  und falsche Antworten.
- Kontrolle: Administratoren definieren, worauf ein Agent zugreifen und was er tun kann. Agenten können nicht auf
  unbefugte Daten zugreifen oder Aktionen außerhalb ihres Workflows ausführen.

## Human-in-the-Loop

Einige Aufgaben erfordern menschliches Urteilsvermögen. Agenten-Workflows können menschliche Aufsicht integrieren. Ein
Agent kann pausieren und auf Ihre Genehmigung warten, bevor er einen Schritt ausführt. Zum Beispiel könnte ein Agent
eine Kundenantwort entwerfen, aber auf die Überprüfung und Genehmigung durch ein Support-Teammitglied warten, bevor er
sie versendet.

Dadurch können Sie Routineaufgaben automatisieren und gleichzeitig die Kontrolle über Entscheidungen behalten.
