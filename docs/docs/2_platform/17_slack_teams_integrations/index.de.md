```markdown
---
title: Slack- und Teams-Integrationen
source_sha: "e29585cc564cba909ac09130467a74bbbfcef6ce92a01bb1ea23ef6b421646db"
---

# Slack- und Teams-Integrationen

## Konzept und Zweck

Die Bot Framework API ist ein separat deploybarer Service, der auf FastAPI basiert und KI-Agent-Funktionalitäten direkt in Kollaborationsplattformen bringt, wo Mitarbeiter täglich arbeiten – Microsoft Teams, Slack und Web-Chat-Oberflächen. Anstatt dass Benutzer zu spezialisierten KI-Anwendungen wechseln müssen, bettet diese Integration intelligente Unterstützung in vertraute Kommunikationstools ein, wodurch Akzeptanzbarrieren beseitigt und die KI-Nutzung in Unternehmen beschleunigt wird.

Dieser Ansatz begegnet einer grundlegenden Herausforderung bei der Einführung von KI in Unternehmen: Selbst leistungsstarke KI-Funktionen bleiben unzureichend genutzt, wenn ihr Zugriff das Erlernen neuer Tools oder die Störung etablierter Workflows erfordert. Indem die Benutzer dort abgeholt werden, wo sie bereits arbeiten, verwandelt die Bot Framework API KI von einer separaten Anwendung in eine integrierte Funktion innerhalb der bestehenden Kollaborationsinfrastruktur.

## Wesentliche Designprinzipien

### Eingebettete KI in natürlichen Workflows

Die Designphilosophie der Plattform priorisiert die Einbettung von KI-Funktionen in Tools, die Mitarbeiter den ganzen Tag über nutzen, anstatt eigenständige KI-Anwendungen zu erstellen. Benutzer interagieren mit KI-Agents über dieselben Teams-Kanäle oder Slack-Konversationen, die sie für die Teamkommunikation verwenden, wodurch Kontextwechsel und der Overhead der Zugangsdatenverwaltung entfallen. Gespräche mit KI-Agents integrieren sich nahtlos neben menschlichen Diskussionen, was natürliche Kollaborationsmuster ermöglicht, bei denen KI-Unterstützung zu einer weiteren Ressource für das Team wird.

Dieser Einbettungsansatz bietet erhebliche Geschäftsvorteile: IT-Abteilungen müssen keine zusätzlichen Anwendungen bereitstellen und unterstützen, Benutzer benötigen keine separate Schulung für KI-spezifische Schnittstellen, KI-Konversationen profitieren von den Sicherheits- und Compliance-Kontrollen, die bereits für Kollaborationsplattformen gelten, und Nutzungsanalysen integrieren sich in bestehende Metriken der Kollaborationsplattformen.

### Mehrkanal-Abstraktion

Durch die Integration mit dem Microsoft Azure Bot Service erhält die Plattform simultanen Zugriff auf mehrere Kommunikationskanäle über eine einzige Implementierung. Azure Bot Service bietet eine standardisierte Abstraktionsschicht, die plattformspezifische Messaging-Protokolle, Authentifizierungsabläufe und Rich-Media-Formatierung handhabt. Diese Architektur ermöglicht es dem Swiss AI Hub, Microsoft Teams, Slack, Web-Chat-Widgets und zukünftige Kanäle zu unterstützen, sobald Azure Bot Service diese hinzufügt, und das alles ohne plattformspezifische Entwicklungsaufwände für jeden Kanal.

Organisationen profitieren von der Deployment-Flexibilität: Verschiedene Teams können ihre bevorzugten Kollaborationstools nutzen, während sie auf identische KI-Funktionen zugreifen; geografische oder regulatorische Anforderungen können durch das Deployment unterschiedlicher Kanäle in verschiedenen Regionen erfüllt werden; und neue Kommunikationsplattformen werden verfügbar, sobald der Bot Service Unterstützung hinzufügt, ohne dass Änderungen an der Swiss AI Hub Plattform erforderlich sind.

### Unabhängiges Deployment und Skalierung

Die Bot Framework API wird als separater Docker-Container unabhängig von den Hauptplattform-Services deployt. Diese architektonische Trennung bietet operationelle Vorteile: Bot-Integration skaliert unabhängig basierend auf Konversationsvolumenmustern, die sich von API-Anfragemustern unterscheiden; Organisationen deployen Bot-Funktionen nur dort, wo sie benötigt werden, und nicht universell; Bot-spezifische Konfiguration und Zugangsdaten bleiben von der Kernplattform-Infrastruktur isoliert; und Updates der Bot-Funktionalität erfolgen, ohne die Kernplattform-Services zu beeinträchtigen oder eine Koordination mit ihnen zu erfordern.

Das unabhängige Deployment-Modell unterstützt auch die Sicherheitsisolation: Bot-Zugangsdaten und Kanal-Konfigurationen bleiben von den Hauptplattform-Secrets getrennt, wodurch der Explosionsradius reduziert wird, falls kanalspezifische Schwachstellen auftreten, und unterschiedliche Sicherheitsrichtlinien für verschiedene Kommunikationskanäle ermöglicht werden.

## Unterstützte Funktionen

Die Bot Framework API ermöglicht eine ausgeklügelte Mensch-KI-Kollaboration durch mehrere Schlüsselfunktionen:

**Konversations-KI-Zugriff**: Benutzer interagieren mit KI-Agents durch natürliche Konversation in ihren Kollaborationstools, wobei sie je nach Aufgabenkomplexität entweder vollständige Antworten oder progressive Streaming-Updates erhalten. Die Schnittstelle unterstützt Rich Media, einschließlich Dokumente, Bilder und strukturierte Datenkarten, und behält den Konversationskontext über mehrere Interaktionen hinweg bei. Dieses kontextbezogene Bewusstsein ermöglicht es Agents, auf frühere Nachrichten zu verweisen, laufende Projekte zu verstehen und relevante Unterstützung basierend auf dem Konversationsverlauf bereitzustellen.

**Multi-Agent-Orchestrierung**: Benutzer können innerhalb derselben Konversation mit verschiedenen spezialisierten Agents interagieren, indem sie je nach Aufgabenanforderungen zwischen Agents wechseln oder Agents explizit für bestimmte Fragen auswählen. Diese Flexibilität unterstützt Workflows, bei denen unterschiedliche Fachgebiete unterschiedliche Agents erfordern – Finanzanalyse, rechtliche Prüfung, technische Recherche – ohne separate Konversationen oder Anwendungen zu benötigen.

**Human-in-the-Loop Workflows**: Das Bot-in-the-Loop-Muster ermöglicht es KI-Agents, während der Ausführung menschliche Eingaben anzufordern, indem sie Fragen in Slack-Kanälen posten, wo Teammitglieder Entscheidungen, Genehmigungen oder fachliche Anleitungen geben können. Agent-Workflows werden nach Erhalt menschlicher Antworten fortgesetzt, was anspruchsvolle Automatisierungsszenarien ermöglicht, die KI-Effizienz mit menschlichem Urteilsvermögen verbinden. Diese Funktion unterstützt Genehmigungs-Workflows, Expertenkonsultationen, Qualitätsprüfungen und Disambiguierungsszenarien, bei denen der menschliche Kontext die geeigneten nächsten Schritte bestimmt.

**Unternehmensintegration**: Die Authentifizierung erfolgt über bestehende organisatorische Identitätsprovider, wodurch sichergestellt wird, dass Benutzer mit denselben Zugangsdaten und Berechtigungen auf die KI zugreifen, die auch den Zugriff auf die Kollaborationsplattform regeln. Konversationen laufen automatisch basierend auf konfigurierbaren Aufbewahrungsrichtlinien ab, was Compliance-Anforderungen ohne manuelles Datenlebenszyklus-Management unterstützt.

## Geschäftswert

### Beschleunigte Akzeptanz und Nutzung

Durch die Eliminierung der Notwendigkeit, separate KI-Anwendungen zu erlernen und darauf zuzugreifen, reduziert die Bot Framework API die Akzeptanzhürden dramatisch. Mitarbeiter beginnen, KI-Unterstützung einfach durch Messaging eines Bots in Teams oder Slack zu nutzen, unter Verwendung von Kommunikationsmustern, die sie bereits kennen. Organisationen berichten von 3-5x höheren Nutzungsraten, wenn KI-Funktionen in bestehende Tools integriert sind, im Vergleich zu eigenständigen KI-Anwendungen, die separaten Zugriff und Schulung erfordern.

Der eingebettete Ansatz kommt insbesondere Gelegenheitsnutzern zugute, die selten, aber signifikant KI-Unterstützung benötigen – diese Benutzer rechtfertigen selten das Erlernen einer separaten Anwendung, nutzen aber bereitwillig Funktionen, die in vertrauten Tools verfügbar sind.

### Operationelle Effizienz durch Mensch-KI-Kollaboration

Das Human-in-the-Loop-Muster ermöglicht es Organisationen, komplexe Prozesse zu automatisieren, während die menschliche Aufsicht an kritischen Entscheidungspunkten beibehalten wird. KI-Agents übernehmen Routineanalysen, Datenerfassung und Entwurfserstellung und eskalieren nur dann an Menschen, wenn Urteilsvermögen oder Genehmigung erforderlich sind. Dieses Kollaborationsmodell bietet Effizienzgewinne durch Automatisierung, während es Rechenschaftspflicht und Qualitätskontrolle durch menschliche Kontrollpunkte bewahrt.

Organisationen implementieren Workflows wie Spesenabrechnungen (KI prüft Richtlinien und markiert Probleme, Menschen genehmigen Ausnahmen), Inhaltsmoderation (KI identifiziert potenzielle Probleme, Menschen treffen endgültige Entscheidungen) und Kundenanfragenbearbeitung (KI entwirft Antworten, Menschen prüfen vor dem Senden), die die Vorteile der Automatisierung mit menschlicher Aufsicht verbinden.

### Reduzierter IT-Overhead

Die Nutzung der bestehenden Kollaborationsplattform-Infrastruktur eliminiert die Anforderungen für das Deployment und die Unterstützung zusätzlicher Anwendungen. IT-Teams müssen keine separaten Authentifizierungssysteme, Benutzerbereitstellung oder Helpdesk-Schulungen für den KI-Zugriff verwalten. Sicherheits- und Compliance-Kontrollen, die bereits für Kollaborationsplattformen gelten – Datenverlustprävention, Aufbewahrungsrichtlinien, Audit-Logging – werden automatisch auf KI-Konversationen angewendet, ohne separate Konfiguration.

Diese Infrastrukturwiederverwendung kommt insbesondere ressourcenbeschränkten Organisationen zugute, bei denen das Deployment und die Unterstützung zusätzlicher Unternehmensanwendungen eine erhebliche Belastung darstellen.

### Deployment-Flexibilität

Das unabhängige Deployment-Modell ermöglicht es Organisationen, Bot-Funktionen selektiv zu deployen – zum Beispiel durch die Aktivierung der Teams-Integration für die Zentrale, während Slack für regionale Büros genutzt wird, oder durch das Deployment von Web-Chat-Widgets für kundenorientierte Szenarien, während Teams intern genutzt wird. Verschiedene Kanäle können an unterschiedliche Agent-Konfigurationen weitergeleitet werden, was die Segmentierung von Anwendungsfällen oder regulatorische Anforderungen unterstützt, bei denen verschiedene Regionen eine unterschiedliche KI-Handhabung erfordern.

## Implementierungsansatz

Als separater, auf FastAPI basierender Service entwickelt, integriert sich die Bot Framework API mit dem Azure Bot Service über plattformspezifische Handler, die Kanalunterschiede verwalten. Der Service verwaltet den Konversationszustand in MongoDB mit konfigurierbaren Aufbewahrungsrichtlinien, während er sich mit dem NATS-Eventsystem der Plattform für bidirektionale Agentenkommunikation verbindet. Eingehende Bot-Aktivitäten werden in Plattform-Events für die Agentenverarbeitung übersetzt, wobei Antworten zurückgestreamt und für jeden Kanal entsprechend formatiert werden. Das zustandslose Design mit persistentem Konversationszustand ermöglicht eine horizontale Skalierung basierend auf dem Konversationsvolumen. Das Deployment als unabhängiger Docker-Container unterstützt eine flexible Infrastrukturplatzierung und ein unabhängiges Versionsmanagement von den Kernplattform-Services. Die Authentifizierung nutzt Azure AD für die Bot-Registrierung, während die Benutzeridentität von Kollaborationsplattformen zu den Plattform-Berechtigungssystemen fließt, wodurch eine konsistente Zugriffskontrolle unabhängig vom Konversationskanal gewährleistet wird.
```
