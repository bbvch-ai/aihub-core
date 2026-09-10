---
title: Agents
source_sha: bde5d4ed5ba5f9fa2ab68f650248091c20a1f6136a92954857241233bd7246b8
---

# Agents

Agents sind spezialisierte KI-Assistenten, die spezifische Aufgaben durch strukturierte Workflows ausführen. Im
Gegensatz zu offenen Chatbots folgen Agents vordefinierten Schritten, um Dokumente zu analysieren, Fragen zu beantworten
oder Geschäftsprozesse abzuschliessen.

Agents können interaktiv (beantworten Benutzerfragen per Chat) oder autonom (führen Aufgaben automatisch nach einem
Zeitplan oder ereignisgesteuert aus) sein. Der strukturierte Workflow-Ansatz macht Agents vorhersehbar, transparent und
auditierbar, unabhängig von ihrer Betriebsweise.

## Was ist ein Agent?

Ein Agent ist ein KI-gestützter Assistent, der konfiguriert ist, um spezifische Aufgaben mithilfe eines vordefinierten
Workflows zu erledigen.

Beispiele:

- Ein HR-Richtlinien-Agent beantwortet Mitarbeiterfragen zu Urlaubsrichtlinien, indem er das Mitarbeiterhandbuch
  konsultiert (interaktiv, Chat-basiert).
- Ein Compliance-Überwachungs-Agent überprüft Dokumente nach einem Zeitplan und markiert potenzielle
  Richtlinienverstösse (autonom, geplant).

Agents kombinieren grosse Sprachmodelle (LLMs) für das Verständnis natürlicher Sprache mit strukturierten Prozessen für
einen zuverlässigen Betrieb.

## Agenten-"Training"

Eine häufige Frage ist, ob Agents mit Unternehmensdaten "trainiert" werden können. Der Swiss AI Hub bietet kein
Modelltraining oder Fine-Tuning an. Agents greifen stattdessen über ihre Wissensdatenbanken auf aktuelle Informationen
zu.

Wenn Leute nach dem Training eines Agents fragen, möchten sie normalerweise, dass der Agent die spezifischen
Informationen ihres Unternehmens kennt. Die Plattform erreicht dies durch Retrieval-Augmented Generation (RAG). Der
Agent ruft relevante Informationen aus Ihrer Wissensdatenbank ab, wenn er Fragen beantwortet, anstatt diese
Informationen direkt im Modell selbst eingebettet zu haben.

Vorteile dieses Ansatzes:

- Informationen bleiben aktuell. Aktualisieren Sie Ihre Dokumente, und Agents verwenden die neuen Informationen sofort
  ohne erneute Verarbeitung.
- Transparenz. Sie können genau sehen, welche Dokumente der Agent zur Beantwortung jeder Frage herangezogen hat.
- Flexibilität. Verschiedene Agents können auf unterschiedliche Untergruppen Ihrer Wissensdatenbank zugreifen, indem Sie
  konfigurieren, welche Sammlungen sie durchsuchen können.

Agents "lernen", indem sie auf eine aktuelle Wissensdatenbank zugreifen, die durch Datenpipelines gepflegt wird. Fügen
Sie neue Dokumente hinzu oder aktualisieren Sie bestehende, und Agents integrieren diese Informationen automatisch.

## Wie Agents funktionieren

Das Verhalten eines Agents folgt einem Workflow, einer vordefinierten Abfolge von Schritten. Dies unterscheidet sich von
allgemeiner Konversations-KI.

Beispiel-Workflow für einen Frage-Antwort-Agenten:

1. Anfrage verstehen: Der Agent verwendet ein LLM, um Ihre Frage zu interpretieren.
2. Informationen abrufen: Der Agent durchsucht eine zugewiesene Wissensdatenbank (z. B. einen SharePoint-Ordner) nach
   relevanten Dokumenten mittels semantischer Suche (RAG).
3. Antwort synthetisieren: Der Agent kombiniert Ihre Frage mit abgerufenen Informationen und generiert eine Antwort.
4. Quellen zitieren: Die Antwort enthält Referenzen zu Quelldokumenten zur Überprüfung.

Vorteile des Workflows:

- Transparenz: Sie können sehen, welche Dokumente der Agent konsultiert hat.
- Zuverlässigkeit: Die Beschränkung des Agenten auf einen Workflow und eine Wissensdatenbank reduziert Halluzinationen
  und falsche Antworten.
- Kontrolle: Administratoren definieren, worauf ein Agent zugreifen und was er tun kann. Agents können nicht auf
  unautorisierte Daten zugreifen oder Aktionen ausserhalb ihres Workflows ausführen.

## Human-in-the-Loop

Einige Aufgaben erfordern menschliches Urteilsvermögen. Agenten-Workflows können menschliche Aufsicht integrieren. Ein
Agent kann pausieren und auf Ihre Genehmigung warten, bevor er einen Schritt ausführt. Zum Beispiel könnte ein Agent
eine Kundenantwort entwerfen, aber warten, bis ein Support-Mitarbeiter sie überprüft und genehmigt, bevor sie gesendet
wird.

Dies ermöglicht Ihnen, Routineaufgaben zu automatisieren, während Sie die Kontrolle über Entscheidungen behalten.

## Verbindung zu externen Tools

Agents sind nicht darauf beschränkt, aus Wissensdatenbanken zu lesen — sie können auch Aktionen in anderen Systemen
ausführen. Über das Model Context Protocol (MCP) verbindet sich ein Agent mit einem externen Tool-Server und nutzt die
von ihm bereitgestellten Tools: Erstellen eines Tickets, Senden einer Nachricht oder Nachschlagen eines Datensatzes in
einer anderen Anwendung.

Eine Verbindung kann sich als der anfragende Benutzer authentifizieren, sodass eine externe Aktion dieser Person und
nicht einem geteilten Service-Konto zugeschrieben wird. Das Audit-Trail und die Benutzerberechtigungen des anderen
Systems bleiben korrekt.
