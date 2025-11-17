---
title: Slack- & Teams-Integrationen
source_sha: b8d3ae16e664e2a47443ffe09787b916f747b748204536d6e7951f3e2cd6946c
---

# Slack- & Teams-Integrationen

## Konzept und Zweck

Die Bot Framework API ist ein separat bereitstellbarer Dienst, der auf FastAPI basiert und KI-Agenten-Fähigkeiten direkt
in Kollaborationsplattformen bringt, auf denen Mitarbeiter täglich arbeiten – Microsoft Teams, Slack und
Web-Chat-Schnittstellen. Anstatt Benutzer dazu zu zwingen, zu spezialisierten KI-Anwendungen zu wechseln, bettet diese
Integration intelligente Unterstützung in vertraute Kommunikationstools ein, wodurch Barrieren für die Akzeptanz
beseitigt und die KI-Nutzung in Unternehmen beschleunigt wird.

Dieser Ansatz begegnet einer grundlegenden Herausforderung bei der Einführung von KI in Unternehmen: Selbst
leistungsstarke KI-Fähigkeiten bleiben ungenutzt, wenn der Zugriff darauf das Erlernen neuer Tools oder die Störung
etablierter Arbeitsabläufe erfordert. Indem sie Benutzer dort abholt, wo sie bereits arbeiten, verwandelt die Bot
Framework API KI von einer separaten Anwendung in eine integrierte Fähigkeit innerhalb der bestehenden
Kollaborationsinfrastruktur.

## Kernprinzipien des Designs

### Eingebettete KI in natürlichen Arbeitsabläufen

Die Designphilosophie der Plattform priorisiert die Einbettung von KI-Fähigkeiten in Tools, die Mitarbeiter den ganzen
Arbeitstag über nutzen, anstatt eigenständige KI-Anwendungen zu erstellen. Benutzer interagieren mit KI-Agenten über
dieselben Teams-Kanäle oder Slack-Konversationen, die sie für die Teamkommunikation verwenden, wodurch Kontextwechsel
und der Aufwand für die Anmeldeverwaltung entfallen. Gespräche mit KI-Agenten integrieren sich nahtlos neben
menschlichen Diskussionen und ermöglichen natürliche Kollaborationsmuster, bei denen KI-Unterstützung zu einer weiteren
Ressource wird, die dem Team zur Verfügung steht.

Dieser Einbettungsansatz bietet erhebliche geschäftliche Vorteile: IT-Abteilungen müssen keine zusätzlichen Anwendungen
bereitstellen und unterstützen, Benutzer benötigen keine separate Schulung für KI-spezifische Schnittstellen,
KI-Konversationen profitieren von den Sicherheits- und Compliance-Kontrollen, die bereits für Kollaborationsplattformen
gelten, und Nutzungsanalysen integrieren sich in bestehende Metriken der Kollaborationsplattform.

### Mehrkanal-Abstraktion

Durch die Integration mit Microsoft Azure Bot Service erhält die Plattform über eine einzige Implementierung
gleichzeitig Zugriff auf mehrere Kommunikationskanäle. Azure Bot Service bietet eine standardisierte
Abstraktionsschicht, die plattformspezifische Messaging-Protokolle, Authentifizierungsabläufe und die Formatierung von
Rich Media verarbeitet. Diese Architektur ermöglicht es dem Swiss AI-Hub, Microsoft Teams, Slack, Web-Chat-Widgets und
zukünftige Kanäle zu unterstützen, sobald Azure Bot Service die Unterstützung hinzufügt, alles ohne plattformspezifische
Entwicklungsaufwände für jeden Kanal.

Organisationen profitieren von der Bereitstellungsflexibilität: Verschiedene Teams können ihre bevorzugten
Kollaborationstools nutzen, während sie auf identische KI-Fähigkeiten zugreifen; geografische oder regulatorische
Anforderungen können durch die Bereitstellung verschiedener Kanäle in verschiedenen Regionen erfüllt werden; und neue
Kommunikationsplattformen werden verfügbar, sobald der Bot Service die Unterstützung hinzufügt, ohne dass Änderungen an
der Swiss AI-Hub-Plattform erforderlich sind.

### Unabhängige Bereitstellung und Skalierung

Die Bot Framework API wird als separater Docker-Container unabhängig von den Hauptplattformdiensten bereitgestellt.
Diese architektonische Trennung bietet betriebliche Vorteile: Die Bot-Integration skaliert unabhängig basierend auf
Mustern des Konversationsvolumens, die sich von API-Anfragemustern unterscheiden; Organisationen stellen Bot-Fähigkeiten
nur dort bereit, wo sie benötigt werden, anstatt universell; Bot-spezifische Konfiguration und Anmeldeinformationen
bleiben von der Kernplattforminfrastruktur isoliert; und Aktualisierungen der Bot-Funktionalität erfolgen, ohne die
Kernplattformdienste zu beeinflussen oder eine Koordination mit ihnen zu erfordern.

Das unabhängige Bereitstellungsmodell unterstützt auch die Sicherheitsisolierung: Bot-Anmeldeinformationen und
Kanalkonfigurationen bleiben von den Hauptplattform-Geheimnissen getrennt, wodurch der Wirkungsbereich reduziert wird,
falls kanalspezifische Schwachstellen auftreten, und unterschiedliche Sicherheitsrichtlinien für verschiedene
Kommunikationskanäle ermöglicht werden.

## Unterstützte Funktionen

Die Bot Framework API ermöglicht eine hochentwickelte Mensch-KI-Zusammenarbeit durch mehrere Schlüsselfunktionen:

**Konversationelle KI-Zugriff**: Benutzer interagieren mit KI-Agenten durch natürliche Konversation in ihren
Kollaborationstools und erhalten entweder vollständige Antworten oder progressive Streaming-Updates, abhängig von der
Komplexität der Aufgabe. Die Schnittstelle unterstützt Rich Media, einschließlich Dokumenten, Bildern und strukturierten
Datenkarten, und behält den Konversationskontext über mehrere Interaktionen hinweg bei. Dieses kontextuelle Bewusstsein
ermöglicht es Agenten, auf frühere Nachrichten zu verweisen, laufende Projekte zu verstehen und relevante Unterstützung
basierend auf dem Konversationsverlauf zu leisten.

**Multi-Agenten-Orchestrierung**: Benutzer können innerhalb derselben Konversation mit verschiedenen spezialisierten
Agenten interagieren, je nach Aufgabenanforderungen zwischen Agenten wechseln oder explizit Agenten für bestimmte Fragen
auswählen. Diese Flexibilität unterstützt Workflows, bei denen verschiedene Fachgebiete unterschiedliche Agenten
erfordern – Finanzanalyse, rechtliche Überprüfung, technische Recherche – ohne separate Konversationen oder Anwendungen
zu benötigen.

**Human-in-the-Loop-Workflows**: Das Bot-in-the-Loop-Muster ermöglicht es KI-Agenten, während der Ausführung
menschlichen Input anzufordern, Fragen in Slack-Kanälen zu stellen, wo Teammitglieder Entscheidungen, Genehmigungen oder
Expertenrat geben können. Agenten-Workflows werden nach Erhalt menschlicher Antworten fortgesetzt, wodurch
hochentwickelte Automatisierungsszenarien ermöglicht werden, die KI-Effizienz mit menschlichem Urteilsvermögen
kombinieren. Diese Fähigkeit unterstützt Genehmigungsworkflows, Expertenkonsultationen, Qualitätskontrollen und
Disambiguierungsszenarien, bei denen der menschliche Kontext die entsprechenden nächsten Schritte bestimmt.

**Unternehmensintegration**: Authentifizierungsabläufe erfolgen über bestehende organisatorische Identitätsanbieter,
wodurch sichergestellt wird, dass Benutzer mit denselben Anmeldeinformationen und Berechtigungen auf KI zugreifen, die
auch den Zugriff auf die Kollaborationsplattform regeln. Konversationen laufen automatisch basierend auf
konfigurierbaren Aufbewahrungsrichtlinien ab, wodurch Compliance-Anforderungen ohne manuelles
Datenlebenszyklus-Management unterstützt werden.

## Geschäftswert

### Beschleunigte Akzeptanz und Nutzung

Indem die Notwendigkeit, separate KI-Anwendungen zu erlernen und darauf zuzugreifen, entfällt, reduziert die Bot
Framework API die Akzeptanzreibung drastisch. Mitarbeiter beginnen, KI-Unterstützung einfach durch das Senden einer
Nachricht an einen Bot in Teams oder Slack zu nutzen, wobei sie Kommunikationsmuster verwenden, die sie bereits kennen.
Organisationen berichten von 3-5x höheren Nutzungsraten, wenn KI-Fähigkeiten in bestehende Tools integriert sind, im
Vergleich zu eigenständigen KI-Anwendungen, die separaten Zugriff und Schulung erfordern.

Der eingebettete Ansatz kommt insbesondere Gelegenheitsnutzern zugute, die KI-Unterstützung selten, aber bedeutsam
benötigen – diese Nutzer rechtfertigen selten das Erlernen einer separaten Anwendung, nutzen aber Fähigkeiten, die in
vertrauten Tools verfügbar sind, gerne.

### Operative Effizienz durch Mensch-KI-Zusammenarbeit

Das Human-in-the-Loop-Muster ermöglicht es Organisationen, komplexe Prozesse zu automatisieren, während die menschliche
Aufsicht an kritischen Entscheidungspunkten aufrechterhalten wird. KI-Agenten übernehmen Routineanalysen, Datenerfassung
und Entwurfserstellung und eskalieren an Menschen nur, wenn Urteilsvermögen oder Genehmigung erforderlich ist. Dieses
Kollaborationsmodell bietet Effizienzgewinne durch Automatisierung und bewahrt gleichzeitig Verantwortlichkeit und
Qualitätskontrolle durch menschliche Kontrollpunkte.

Organisationen implementieren Workflows wie Spesenabrechnung (KI prüft Richtlinien und kennzeichnet Probleme, Menschen
genehmigen Ausnahmen), Inhaltsmoderation (KI identifiziert potenzielle Probleme, Menschen treffen die endgültigen
Entscheidungen) und Bearbeitung von Kundenanfragen (KI entwirft Antworten, Menschen überprüfen vor dem Senden), die
Automatisierungsvorteile mit menschlicher Aufsicht kombinieren.

### Reduzierter IT-Overhead

Die Nutzung der bestehenden Kollaborationsplattform-Infrastruktur eliminiert die Notwendigkeit, zusätzliche Anwendungen
bereitzustellen und zu unterstützen. IT-Teams müssen keine separaten Authentifizierungssysteme, Benutzerbereitstellung
oder Helpdesk-Schulungen für den KI-Zugriff verwalten. Sicherheits- und Compliance-Kontrollen, die bereits für
Kollaborationsplattformen gelten – Verhinderung von Datenverlust, Aufbewahrungsrichtlinien, Audit-Logging – gelten
automatisch für KI-Konversationen ohne separate Konfiguration.

Diese Infrastrukturwiederverwendung kommt insbesondere ressourcenbeschränkten Organisationen zugute, bei denen die
Bereitstellung und Unterstützung zusätzlicher Unternehmensanwendungen eine erhebliche Belastung erzeugt.

### Bereitstellungsflexibilität

Das unabhängige Bereitstellungsmodell ermöglicht es Organisationen, Bot-Fähigkeiten selektiv bereitzustellen –
beispielsweise die Teams-Integration für die Zentrale zu aktivieren, während Slack für regionale Büros verwendet wird,
oder Web-Chat-Widgets für kundenorientierte Szenarien bereitzustellen, während Teams intern genutzt wird. Verschiedene
Kanäle können an unterschiedliche Agentenkonfigurationen weitergeleitet werden, was eine Anwendungsfallsegmentierung
oder regulatorische Anforderungen unterstützt, bei denen verschiedene Regionen unterschiedliche KI-Handhabung erfordern.

## Implementierungsansatz

Als separater FastAPI-basierter Dienst entwickelt, integriert sich die Bot Framework API mit Azure Bot Service über
plattformspezifische Handler, die Kanalunterschiede verwalten. Der Dienst verwaltet den Konversationszustand in MongoDB
mit konfigurierbaren Aufbewahrungsrichtlinien und verbindet sich mit dem NATS-Ereignissystem der Plattform für die
bidirektionale Agentenkommunikation. Eingehende Bot-Aktivitäten werden in Plattformereignisse zur Agentenverarbeitung
übersetzt, wobei die Antworten zurückgestreamt und für jeden Kanal entsprechend formatiert werden. Das zustandslose
Design mit persistentem Konversationszustand ermöglicht eine horizontale Skalierung basierend auf dem
Konversationsvolumen. Die Bereitstellung als unabhängiger Docker-Container unterstützt eine flexible
Infrastrukturplatzierung und eine unabhängige Versionsverwaltung von den Kernplattformdiensten. Die Authentifizierung
nutzt Azure AD für die Bot-Registrierung, während die Benutzeridentität von Kollaborationsplattformen in die
Plattform-Berechtigungssysteme fließt, wodurch eine konsistente Zugriffssteuerung unabhängig vom Konversationskanal
gewährleistet wird.
