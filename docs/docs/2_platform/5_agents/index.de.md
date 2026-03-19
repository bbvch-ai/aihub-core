```markdown
---
title: Agents
source_sha: "1a7efc2f6e84e15eada1847e47f85e6ba8d26dab480c799a503863eebebba46e"
---

# Agents

Agents sind spezialisierte KI-Assistenten, die bestimmte Aufgaben über strukturierte Workflows ausführen. Im Gegensatz zu offenen Chatbots folgen Agents vordefinierten Schritten, um Dokumente zu analysieren, Fragen zu beantworten oder Geschäftsprozesse abzuschliessen.

Agents können interaktiv sein (Benutzerfragen per Chat beantworten) oder autonom (Aufgaben automatisch nach einem Zeitplan oder durch Ereignisse ausgelöst ausführen). Der strukturierte Workflow-Ansatz macht Agents unabhängig von ihrer Betriebsweise vorhersagbar, transparent und auditierbar.

## Was ist ein Agent?

Ein Agent ist ein KI-gestützter Assistent, der für die Bearbeitung spezifischer Aufgaben unter Verwendung eines vordefinierten Workflows konfiguriert ist.

Beispiele:

- Ein HR-Richtlinien-Agent beantwortet Mitarbeiterfragen zu Urlaubsrichtlinien, indem er das Mitarbeiterhandbuch konsultiert (interaktiv, chatbasiert).
- Ein Compliance-Monitoring-Agent überprüft Dokumente nach einem Zeitplan und markiert potenzielle Richtlinienverstösse (autonom, geplant).

Agents kombinieren grosse Sprachmodelle (LLMs) zum Verständnis natürlicher Sprache mit strukturierten Prozessen für einen zuverlässigen Betrieb.

## Agenten-„Training“

Eine häufige Frage ist, ob Agents auf Unternehmensdaten „trainiert“ werden können. Der Swiss AI Hub bietet kein Modelltraining oder Fine-Tuning an. Stattdessen greifen Agents über ihre Wissensdatenbanken auf aktuelle Informationen zu.

Wenn Personen nach dem Training eines Agents fragen, möchten sie in der Regel, dass der Agent die spezifischen Informationen ihres Unternehmens kennt. Die Plattform erreicht dies durch Retrieval-Augmented Generation (RAG). Der Agent ruft relevante Informationen aus Ihrer Wissensdatenbank ab, wenn er Fragen beantwortet, anstatt diese Informationen direkt im Modell eingebettet zu haben.

Vorteile dieses Ansatzes:

- Informationen bleiben aktuell. Aktualisieren Sie Ihre Dokumente, und Agents verwenden die neuen Informationen sofort ohne erneute Verarbeitung.
- Transparenz. Sie können genau sehen, welche Dokumente der Agent zur Beantwortung jeder Frage herangezogen hat.
- Flexibilität. Verschiedene Agents können auf unterschiedliche Teilmengen Ihrer Wissensdatenbank zugreifen, indem Sie konfigurieren, welche Sammlungen sie durchsuchen können.

Agents „lernen“, indem sie auf eine aktuelle Wissensdatenbank zugreifen, die über Daten-Pipelines gepflegt wird. Fügen Sie neue Dokumente hinzu oder aktualisieren Sie bestehende, und Agents integrieren diese Informationen automatisch.

## Wie Agents funktionieren

Das Verhalten eines Agents folgt einem Workflow, einer vordefinierten Abfolge von Schritten. Dies unterscheidet sich von allgemeiner konversationeller KI.

Beispiel-Workflow für einen Fragen-Antworten-Agenten:

1. Anfrage verstehen: Der Agent verwendet ein LLM, um Ihre Frage zu interpretieren.
2. Informationen abrufen: Der Agent durchsucht eine festgelegte Wissensdatenbank (z. B. einen SharePoint-Ordner) nach relevanten Dokumenten mittels semantischer Suche (RAG).
3. Antwort synthetisieren: Der Agent kombiniert Ihre Frage mit abgerufenen Informationen und generiert eine Antwort.
4. Quellen angeben: Die Antwort enthält Verweise auf Quelldokumente zur Überprüfung.

Vorteile des Workflows:

- Transparenz: Sie können sehen, welche Dokumente der Agent konsultiert hat.
- Zuverlässigkeit: Die Begrenzung des Agents auf einen Workflow und eine Wissensdatenbank reduziert Halluzinationen und falsche Antworten.
- Kontrolle: Administratoren definieren, worauf ein Agent zugreifen und was er tun kann. Agents können nicht auf unbefugte Daten zugreifen oder Aktionen ausserhalb ihres Workflows ausführen.

## Human-in-the-Loop

Einige Aufgaben erfordern menschliches Urteilsvermögen. Agenten-Workflows können menschliche Aufsicht integrieren. Ein Agent kann pausieren und auf Ihre Genehmigung warten, bevor er einen Schritt ausführt. Zum Beispiel könnte ein Agent eine Kundenantwort entwerfen, aber warten, bis ein Support-Teammitglied sie überprüft und genehmigt hat, bevor sie gesendet wird.

Dadurch können Sie Routineabläufe automatisieren und gleichzeitig die Kontrolle über Entscheidungen behalten.
```
