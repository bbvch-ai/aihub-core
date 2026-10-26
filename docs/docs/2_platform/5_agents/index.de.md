---
title: Agents
source_sha: 24f5cd1fe74af91a65ebfe580edea49ef825185fb61831c60696c74e077a983a
---

# Agents

Agents sind spezialisierte KI-Assistenten, die spezifische Aufgaben durch strukturierte Workflows ausführen. Im
Gegensatz zu offenen Chatbots folgen Agents vordefinierten Schritten, um Dokumente zu analysieren, Fragen zu beantworten
oder Geschäftsprozesse abzuschliessen.

Agents können interaktiv (beantworten Benutzerfragen per Chat) oder autonom (führen Aufgaben automatisch nach einem
Zeitplan oder ereignisgesteuert aus) sein. Der strukturierte Workflow-Ansatz macht Agents vorhersehbar, transparent und
auditierbar, unabhängig von ihrer Betriebsweise. Wo eine Aufgabe es erfordert, lässt der Universal Agent das Modell
unter den Werkzeugen wählen, die Sie aktiviert haben, weiterhin innerhalb der Grenzen, Berechtigungen und Freigaben, die
Sie festlegen.

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

## Das Standard-Blueprint-Set

Die folgenden Seiten dokumentieren jeden Agent-Blueprint, den die Plattform mitliefert. Ein Mandant erhält nicht alle
davon.

Drei werden einem neuen Mandanten standardmässig freigegeben:

- **Anweisungsbasierter Assistent** — folgt Anweisungen in Klartext, die Sie schreiben
- **Belehrbarer Assistent** — lernt aus Beispielen, welche Form der Antwort Sie wünschen
- **Dokumenten-Intelligenz-Assistent** — antwortet aus Ihren Wissensdatenbanken und nennt seine Quellen

Der Universal Agent ist das eine Profil, das ein Administrator einmal für offene Aufgaben konfiguriert: Das Modell
entscheidet pro Nachricht, ob es Wissen durchsucht, die angehängten Dateien des Benutzers liest, sich an Gespeichertes
erinnert oder ein anderes aktiviertes Werkzeug nutzt. Der Wissensextraktions-Agent sammelt Datensätze aus vielen
Dokumenten in einer Tabelle, jede Zeile mit ihrer Datei.

Die übrigen sind hier dokumentiert, weil sie gebaut, unterstützt und einsatzbereit sind — ein Mandant sieht einen davon
aber erst, nachdem ein Sysadmin ihn freigegeben hat. So bleibt der Katalog eines neuen Mandanten klein genug für eine
Auswahl, ohne einem Mandanten etwas wegzunehmen, der bereits auf einen Agenten ausserhalb des Sets setzt. Eine Freigabe
wirkt sofort, ohne erneutes Deployment; siehe [Zugriffskontrolle](../16_multi_tenancy/4_access_control/).

## Was jeder Chat-Agent kann

Die Konversations-Blueprints, die auf den gemeinsamen Fähigkeiten aufbauen (Anweisungsbasierter, Belehrbarer und
Dokumenten-Intelligenz-Assistent, Agent für Unternehmenswissen, MCP Tool Agent und Universal Agent), verhalten sich in
der Unterhaltung gleich:

- **Angehängte Dateien.** Im Chat angehängte Dateien liest der Agent selbst und führt sie als Quellen auf. Eine lange
  Datei wird auf die Abschnitte gekürzt, die für die Frage wichtig sind, und die Antwort sagt das.
- **Wissensverweise.** Die Eingabe von `#` in Open WebUI verweist den Agenten auf eine der Wissenssammlungen des
  Unternehmens, beschränkt auf das, was der Benutzer lesen darf.
- **Inline-Zitate.** Aussagen verlinken auf das Dokument, aus dem sie stammen, als nummerierte Chips in der Antwort.
- **Gedächtnis.** Was der Agent über den Benutzer und die Organisation weiss, fliesst in die Anweisungen des Modells
  ein.
- **Chat-Umschalter.** Ein Chat-Umschalter ist eine Anfrage an den Agenten, der sie als nachverfolgte, kostenzugeordnete
  Schritte ausführt. Ein Agent zeigt einen Umschalter nur, wenn er ihn bedienen kann; heute sind das Code Interpreter
  und My Files beim Universal Agent.
- **Ablehnungen statt Fehler.** Eine Nachricht, die grösser ist als das Kontextfenster des Modells, oder eine Anfrage
  ausserhalb des Aufgabenbereichs eines Belehrbaren Assistenten wird im Chat mit einer kurzen Erklärung statt mit einem
  Fehler beantwortet.

Wie dies in Open WebUI erscheint, ist unter [Integrationsarchitektur](../10_chat_ui/11_integration_architecture/)
beschrieben; die Einstellungen finden Sie unter [Blueprints & Profile](2_blueprints_and_profiles/#shared-chat-settings).

## Werkzeuge, die das Modell wählt

Ein fester Workflow ist der Standard, weil er vorhersehbar ist. Manche Aufgaben lassen sich nicht als feste Abfolge
schreiben, daher kann ein Agent dem Modell auch eine Reihe von Werkzeugen übergeben und es pro Nachricht entscheiden
lassen, welche es verwendet, sie ausführen und erneut entscheiden, bis es antworten kann. Das ist die Werkzeugschleife,
und so arbeitet der Universal Agent.

Die Schleife bleibt innerhalb von Kontrollen, die ein Administrator pro Profil festlegt:

- **Nur Angebotenes wird ausgeführt.** Ein Werkzeug wird nur angeboten, wenn das Profil es aktiviert, der Zugriff des
  Benutzers es erlaubt und, bei Code Interpreter oder My Files, der Chat-Umschalter eingeschaltet ist. Ein Aufruf von
  etwas anderem wird abgelehnt.
- **Freigaben.** Ein Werkzeug kann den Benutzer zuerst um Bestätigung bitten: bei jedem Aufruf, einmal pro Antwort oder
  einmal pro Unterhaltung. Ein abgelehntes Werkzeug wird für diese Antwort nicht erneut angefragt.
- **Grenzen.** Das Profil begrenzt die Anzahl der Entscheidungen und Werkzeugaufrufe. An der Grenze antwortet das Modell
  mit dem, was es hat, und der Chat zeigt an, dass es vorzeitig aufgehört hat.
- **Transparenz.** Jeder Aufruf und jedes Ergebnis erscheint im Chat und in der Event-Historie, sodass der Weg zu einer
  Antwort wie jeder Workflow auditiert werden kann.

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
