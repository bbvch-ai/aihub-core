---
title: Kernkomponenten
source_sha: "734bd788a0afd9456ad333bffb52d727c353a9c66c0552df1b652709fd6b8aca"
---

# Kernkomponenten

Der Swiss AI Hub ist eine vollständige Plattform, die Infrastruktur für Agents, Pipelines und Prozessautomatisierung umfasst. Das hier beschriebene Stufenmodell (Tier-Modell) ist ein empfohlener Einführungspfad und keine Sammlung separater Softwareversionen.

Organisationen stehen oft vor Herausforderungen, wenn sie komplexe Automatisierungsprojekte in Angriff nehmen, ohne zuvor eine grundlegende KI-Kompetenz aufzubauen. Das Stufenmodell bietet einen strukturierten Ansatz, der sich an erfolgreichen Einführungsmustern orientiert.

**Tier 1** bietet jedem in der Organisation sicheren LLM-Zugriff. Durch direkte Erfahrung lernen die Benutzer die Fähigkeiten und Grenzen der Modelle kennen, verbessern ihre Prompt-Schreibfähigkeiten und identifizieren Aufgaben in ihrer täglichen Arbeit, bei denen KI von Vorteil sein könnte.

Nach einer gewissen Nutzungsdauer wird die Reibung durch den Wechsel zwischen Arbeitsanwendungen und einer dedizierten KI-Oberfläche zu einer häufigen Beschwerde. Dies führt zu **Tier 1+**, welches dieselben KI-Funktionen direkt in Tools wie Microsoft Teams, Slack und Outlook integriert. Dies reduziert Workflow-Unterbrechungen und fördert eine breitere Akzeptanz.

Benutzer könnten dann feststellen, dass den generischen Modellen ein spezifischer Unternehmenskontext fehlt. Zum Beispiel wäre ein Modell, das eine Stellenbewerbung bewerten soll, sich der internen Einstellungspolitik einer Organisation nicht bewusst. Dies signalisiert die Bereitschaft für **Tier 2**.

**Tier 2** führt spezialisierte Agents ein, die Zugriff auf organisationales Wissen erhalten. Ein HR-Agent kann so konfiguriert werden, dass er Einstellungskriterien aus Mitarbeiterhandbüchern versteht. Ein Finanz-Agent kann mit dem Kontenplan des Unternehmens vertraut gemacht werden, um Finanzsysteme abzufragen. Diese Agents nutzen die spezifischen Daten einer Organisation, um relevante, kontextbezogene Antworten zu liefern.

Mit zunehmender Agent-Nutzung treten repetitive Orchestrierungsmuster auf. Ein Mitarbeiter könnte ein Dokument manuell zur Analyse an einen Agent weiterleiten, dann zur Überprüfung an einen Manager und schließlich an einen weiteren Agent für eine Hintergrundprüfung. Diese Art der mehrstufigen, manuellen Weiterleitung deutet auf die Notwendigkeit von **Tier 3** hin.

**Tier 3** automatisiert diese Muster als formale Prozesse. Das System kann so konfiguriert werden, dass es Stellenbewerbungen aufnimmt, diese zur Vorauswahl an einen HR-Agent weiterleitet, eine menschliche Überprüfung nur für Grenzfälle anfordert, Hintergrundprüfungen über externe Systeme auslöst und die zuständigen Personalverantwortlichen benachrichtigt. Dies ermöglicht es menschlichen Mitarbeitern, sich auf die Entscheidungsfindung und die Behandlung von Ausnahmen zu konzentrieren.

Die Plattform umfasst alle diese Funktionen von Anfang an. Das Stufenmodell beantwortet die Frage, wann jede Funktion basierend auf der organisatorischen Bereitschaft eingeführt werden sollte. Die Progression gibt den Mitarbeitern Zeit, Workflows anzupassen, Fähigkeiten zu entwickeln und Vertrauen in das System aufzubauen.

## Tier 1: Grundlage für sicheren KI-Zugriff

![Tier 1 Architecture](../../../../media/architecture/high_level/tier_1.png)

Der primäre Zugangspunkt für Benutzer ist die Open-WebUI Weboberfläche, die Text-, Dokument- und Spracheingaben unterstützt.

Alle Anfragen werden über eine API-Schicht verarbeitet, die Authentifizierung handhabt, Berechtigungen für das angefragte Modell überprüft und die Interaktion zur Überprüfung protokolliert. Die Anfrage wird dann, basierend auf der Systemkonfiguration, an das entsprechende LLM, wie ein OpenAI- oder Google Gemini-Modell, weitergeleitet.

Antworten vom LLM werden mithilfe von Server-Sent Events an den Browser zurückgestreamt, sodass der Benutzer den Text sehen kann, während er generiert wird. Diese Architektur gewährleistet eine reaktionsschnelle Oberfläche, selbst bei Abfragen, die längere Verarbeitungszeiten erfordern.

Eine separate Admin UI, erstellt mit Nuxt, bietet Administratoren Einblick in die Systemnutzung, Benutzerverwaltung und Modellkonfiguration. Sie ermöglicht es ihnen, die Modellnutzung zu überwachen, Kostenlimits festzulegen und Audit-Logs zu überprüfen.

Alle Daten, einschließlich Benutzeranfragen, LLM-Antworten, Konversationsverlauf und Systemprotokolle, werden in der internen Datenbank der Plattform gespeichert. Dies stellt sicher, dass die Daten innerhalb der kontrollierten Infrastruktur der Organisation verbleiben, es sei denn, der externe Modellzugriff ist explizit konfiguriert.

## Tier 1+: Benutzer dort abholen, wo sie arbeiten

![Tier 1+ Architecture](../../../../media/architecture/high_level/tier_1_plus.png)

Die Einschränkung einer eigenständigen Weboberfläche ist die Workflow-Unterbrechung, die durch den Kontextwechsel verursacht wird. Tier 1+ löst dies, indem es die Funktionen der Plattform in die Anwendungen erweitert, die Mitarbeiter täglich nutzen. Ein Benutzer in Microsoft Teams kann einen Konversationsverlauf direkt in der Anwendung zusammenfassen, und die Antwort der KI erscheint im selben Kanal.

::: details Unterstützte Kanäle
Die Plattform nutzt das Azure Bot Framework für Integrationen. Unterstützte Kanäle sind:

- Alexa
- E-Mail
- Facebook
- MS Teams
- Outlook
- Skype
- Slack
- Telegram
- WeChat
- Web
- ... und mehr
:::

Jede Integration passt sich den Interaktionsmustern des Host-Tools an. Zum Beispiel könnte eine KI-Antwort in Slack in einem Thread gepostet werden, während sie in Outlook beim Verfassen von E-Mail-Antworten unterstützen könnte. Die zentrale API-Schicht stellt sicher, dass alle Interaktionen, unabhängig von ihrem Ursprung, denselben Sicherheits-, Governance- und Logging-Richtlinien unterliegen.

## Tier 2: Von Daten zu kontextbezogener Intelligenz

![Tier 2 Architecture](../../../../media/architecture/high_level/tier_2.png)

Tier 2 führt Funktionen zur Aufnahme und Strukturierung von Organisationsdaten ein, um KI-Agents Kontext bereitzustellen. Der Prozess beginnt mit Informationsquellen wie SharePoint-Dokumentbibliotheken.

Eine Pipeline orchestriert den Datenverarbeitungs-Workflow. Sie überwacht verbundene Quellen auf neue oder aktualisierte Dateien und löst eine Verarbeitungssequenz aus. Dokumente werden geparst, um nicht nur Text, sondern auch strukturelle Elemente wie Überschriften und Tabellen zu extrahieren. Der Inhalt wird dann basierend auf Themenwechseln oder Abschnittstrennungen in semantisch bedeutungsvolle Chunks unterteilt. Jeder Chunk wird mithilfe eines Modells wie Mistral in ein Vektor-Embedding umgewandelt.

::: tip
Die hier beschriebene Pipeline ist eine Standardkonfiguration. Das SDK ermöglicht die Erstellung benutzerdefinierter Pipelines, um Verbindungen zu anderen Quellen (Datenbanken, APIs, FTP-Server) herzustellen, die Dokumentverarbeitung anzupassen und Daten anzureichern.
:::

Diese Embeddings werden in einer Vektordatenbank gespeichert und indiziert, die als Wissensbasis der Plattform dient. Dies ermöglicht die semantische Suche, wodurch Agents Informationen basierend auf ihrer Bedeutung und nicht auf exakten Schlüsselwortübereinstimmungen abrufen können. Das System pflegt eine klare Herkunft jedes Embeddings zurück zu seinem Quelldokument für Rückverfolgbarkeit und Verifikation.

Mit einer etablierten Wissensbasis kann die Plattform mehrere Agents unterstützen. Standard-Agents könnten einen Dokumentenanalysten oder einen Dateninterpretierer umfassen. Benutzerdefinierte Agents können mit dem SDK erstellt werden, um organisationsspezifische Aufgaben zu bearbeiten, interne Terminologie zu verstehen oder domänenspezifische Logik anzuwenden.

Die Plattform ist auch mittels Model Context Protocol (MCP) offen für die Außenwelt. Durch MCP können Agents von anderen Systemen sicher auf die Plattform und deren Agents zugreifen.

## Tier 3: Orchestrierung von Geschäftsprozessen

![Tier 3 Architecture](../../../../media/architecture/high_level/tier_3.png)

Tier 3 führt eine Prozess-Orchestrierungs-Engine ein, um mehrstufige Workflows zu automatisieren, die KI-Agents, Menschen und externe Systeme involvieren.

Eine dedizierte Process UI ermöglicht es Benutzern, diese Workflows zu visualisieren und mit ihnen zu interagieren. Sie zeigt aktive Prozesse als Flussdiagramme an, die den aktuellen Schritt, die verantwortliche Entität (Mensch, Agent oder externes System) und die nachfolgenden Schritte darstellen.

Wenn ein Prozess ausgelöst wird, evaluiert die Orchestrierungs-Engine den ersten Schritt. Erfordert der Schritt eine Dokumentenanalyse, wird die Aufgabe an einen KI-Agent delegiert. Die Ausgabe des Agents wird an den Orchestrator zurückgegeben, der dann mit dem nächsten Schritt fortfährt. Erfordert ein Schritt menschliches Urteilsvermögen, wird eine Aufgabe im Arbeitsbereich des jeweiligen Benutzers in der Process UI erstellt. Die Oberfläche stellt die Analyse der KI, das Quelldokument und den Kontext für die Entscheidung bereit. Sobald der Mensch die Aufgabe abgeschlossen hat, wird der Prozess fortgesetzt.

Externe Systeme können über Konnektoren integriert werden. Power Automate-Verbindungen können Flows auslösen, um SharePoint-Listen zu aktualisieren oder E-Mails zu senden. Eine n8n-Integration ermöglicht die Kommunikation mit UiPath für Aufgaben der Robotic Process Automation, die Legacy-Systeme betreffen.

::: tip
Der hier beschriebene Prozess ist ein Beispiel. Das SDK kann verwendet werden, um benutzerdefinierte Prozesse zu erstellen, die Verbindungen zu verschiedenen externen und internen Systemen herstellen.
:::

Die Orchestrierungs-Engine verwaltet den Zustand jedes Prozesses, handhabt Timeouts und Fehler. Wenn ein externes System nicht reagiert, kann der Prozess so konfiguriert werden, dass die Aufgabe zur manuellen Intervention an einen Menschen weitergeleitet wird. Die API-Schicht wird in dieser Stufe erweitert, um Konversationskontexte zu verwalten, die mehrere Teilnehmer und lange Zeiträume umfassen.
