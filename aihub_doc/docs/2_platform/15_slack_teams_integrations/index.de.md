---
title: Slack & Teams Integrationen
index: 15
source_sha: "022b9a660d58ac3c20b1d53e89f460d18b16d0b56aa9ebe5b93e3a71d852c6c9"
---

# Slack & Teams Integrationen

## Konzept und Zweck

Die Bot Framework API ist ein separat deploybarer Dienst, der auf FastAPI basiert und die Fähigkeiten von KI-Agenten direkt in Kollaborationsplattformen integriert, in denen Mitarbeiter täglich arbeiten – Microsoft Teams, Slack und Web-Chat-Oberflächen. Anstatt Benutzer zum Wechsel zu spezialisierten KI-Anwendungen zu zwingen, bettet diese Integration intelligente Unterstützung in vertraute Kommunikationstools ein, wodurch Einführungshürden beseitigt und die KI-Nutzung in Unternehmen beschleunigt wird.

Dieser Ansatz begegnet einer grundlegenden Herausforderung bei der Einführung von KI in Unternehmen: Selbst leistungsstarke KI-Fähigkeiten bleiben ungenutzt, wenn der Zugriff auf sie das Erlernen neuer Tools oder die Unterbrechung etablierter Arbeitsabläufe erfordert. Indem sie Benutzer dort abholt, wo sie bereits arbeiten, verwandelt die Bot Framework API KI von einer separaten Anwendung in eine integrierte Fähigkeit innerhalb der bestehenden Kollaborationsinfrastruktur.

## Zentrale Designprinzipien

### Eingebettete KI in natürlichen Arbeitsabläufen

Die Designphilosophie der Plattform priorisiert die Einbettung von KI-Funktionen in Tools, die Mitarbeiter während ihres Arbeitstages verwenden, anstatt eigenständige KI-Anwendungen zu erstellen. Benutzer interagieren mit KI-Agenten über dieselben Teams-Kanäle oder Slack-Konversationen, die sie für die Teamkommunikation nutzen, wodurch Kontextwechsel und der Overhead für die Anmeldeinformationen entfallen. Konversationen mit KI-Agenten integrieren sich nahtlos neben menschlichen Diskussionen und ermöglichen natürliche Kollaborationsmuster, bei denen KI-Unterstützung zu einer weiteren Ressource wird, die dem Team zur Verfügung steht.

Dieser Einbettungsansatz bietet erhebliche geschäftliche Vorteile: IT-Abteilungen müssen keine zusätzlichen Anwendungen bereitstellen und unterstützen, Benutzer benötigen keine separate Schulung für KI-spezifische Schnittstellen, KI-Konversationen profitieren von den Sicherheits- und Compliance-Kontrollen, die bereits für Kollaborationsplattformen gelten, und Nutzungsanalysen integrieren sich in bestehende Metriken der Kollaborationsplattform.

### Multi-Channel-Abstraktion

Durch die Integration mit dem Microsoft Azure Bot Service erhält die Plattform über eine einzige Implementierung simultanen Zugriff auf mehrere Kommunikationskanäle. Der Azure Bot Service bietet eine standardisierte Abstraktionsschicht, die plattformspezifische Messaging-Protokolle, Authentifizierungsabläufe und die Formatierung von Rich Media handhabt. Diese Architektur ermöglicht es dem Swiss AI-Hub, Microsoft Teams, Slack, Web-Chat-Widgets und zukünftige Kanäle zu unterstützen, sobald der Azure Bot Service die Unterstützung hinzufügt, alles ohne plattformspezifischen Entwicklungsaufwand für jeden Kanal.

Organisationen profitieren von der Bereitstellungsflexibilität: Verschiedene Teams können ihre bevorzugten Kollaborationstools nutzen, während sie auf identische KI-Funktionen zugreifen; geografische oder regulatorische Anforderungen können durch die Bereitstellung verschiedener Kanäle in unterschiedlichen Regionen erfüllt werden; und neue Kommunikationsplattformen werden verfügbar, sobald der Bot Service die Unterstützung hinzufügt, ohne dass Änderungen an der Swiss AI-Hub Plattform erforderlich sind.

### Unabhängige Bereitstellung und Skalierung

Die Bot Framework API wird als separater Docker-Container unabhängig von den Hauptplattformdiensten bereitgestellt. Diese architektonische Trennung bietet operative Vorteile: Die Bot-Integration skaliert unabhängig basierend auf Konversationsvolumenmustern, die sich von API-Anfragemustern unterscheiden; Organisationen stellen Bot-Fähigkeiten nur dort bereit, wo sie benötigt werden, anstatt universell; botspezifische Konfigurationen und Anmeldeinformationen bleiben von der Kernplattforminfrastruktur isoliert; und Aktualisierungen der Bot-Funktionalität erfolgen, ohne die Kernplattformdienste zu beeinflussen oder eine Koordination mit ihnen zu erfordern.

Das unabhängige Bereitstellungsmodell unterstützt auch die Sicherheitsisolation: Bot-Anmeldeinformationen und Kanalkonfigurationen bleiben von den Hauptplattform-Geheimnissen getrennt, wodurch der potenzielle Schadensradius reduziert wird, falls kanalspezifische Schwachstellen auftreten, und unterschiedliche Sicherheitsrichtlinien für verschiedene Kommunikationskanäle ermöglicht werden.

## Unterstützte Funktionen

Die Bot Framework API ermöglicht eine ausgeklügelte Mensch-KI-Zusammenarbeit durch mehrere Schlüsselfunktionen:

**Konversationsbasierter KI-Zugriff**: Benutzer interagieren mit KI-Agenten durch natürliche Konversation in ihren Kollaborationstools und erhalten je nach Aufgabenkomplexität entweder vollständige Antworten oder progressive Streaming-Updates. Die Schnittstelle unterstützt Rich Media, einschließlich Dokumente, Bilder und strukturierte Datenkarten, und behält den Konversationskontext über mehrere Interaktionen hinweg bei. Dieses kontextbezogene Verständnis ermöglicht es Agenten, auf frühere Nachrichten zu verweisen, laufende Projekte zu verstehen und relevante Unterstützung basierend auf dem Konversationsverlauf bereitzustellen.

**Multi-Agenten-Orchestrierung**: Benutzer können innerhalb derselben Konversation mit verschiedenen spezialisierten Agenten interagieren, Agenten je nach Aufgabenanforderungen wechseln oder Agenten explizit für bestimmte Fragen auswählen. Diese Flexibilität unterstützt Workflows, bei denen unterschiedliche Fachgebiete unterschiedliche Agenten erfordern – Finanzanalyse, Rechtsprüfung, technische Recherche –, ohne separate Konversationen oder Anwendungen zu benötigen.

**Human-in-the-Loop-Workflows**: Das Bot-in-the-Loop-Muster ermöglicht es KI-Agenten, während der Ausführung menschliche Eingaben anzufordern, indem sie Fragen in Slack-Kanälen stellen, wo Teammitglieder Entscheidungen, Genehmigungen oder Expertenratschläge geben können. Agenten-Workflows werden nach Erhalt menschlicher Antworten fortgesetzt, was ausgeklügelte Automatisierungsszenarien ermöglicht, die KI-Effizienz mit menschlichem Urteilsvermögen kombinieren. Diese Fähigkeit unterstützt Genehmigungsworkflows, Expertenkonsultationen, Qualitätsprüfungen und Disambiguierungsszenarien, bei denen der menschliche Kontext die geeigneten nächsten Schritte bestimmt.

**Unternehmensintegration**: Authentifizierungsabläufe erfolgen über bestehende Organisations-Identitätsprovider, wodurch sichergestellt wird, dass Benutzer mit denselben Anmeldeinformationen und Berechtigungen auf KI zugreifen, die den Zugriff auf die Kollaborationsplattform regeln. Konversationen laufen automatisch basierend auf konfigurierbaren Aufbewahrungsrichtlinien ab, was Compliance-Anforderungen ohne manuelle Datenlebenszyklusverwaltung unterstützt.

## Geschäftswert

### Beschleunigte Einführung und Nutzung

Durch die Eliminierung der Notwendigkeit, separate KI-Anwendungen zu erlernen und darauf zuzugreifen, reduziert die Bot Framework API die Einführungshürden dramatisch. Mitarbeiter beginnen mit der Nutzung von KI-Unterstützung, indem sie einfach einen Bot in Teams oder Slack anschreiben und dabei Kommunikationsmuster verwenden, die sie bereits kennen. Organisationen berichten von 3-5x höheren Nutzungsraten, wenn KI-Funktionen in bestehende Tools integriert sind, verglichen mit eigenständigen KI-Anwendungen, die separaten Zugriff und Schulung erfordern.

Der eingebettete Ansatz kommt insbesondere gelegentlichen Benutzern zugute, die selten, aber signifikant KI-Unterstützung benötigen – diese Benutzer rechtfertigen selten das Erlernen einer separaten Anwendung, nutzen aber bereitwillig Funktionen, die in vertrauten Tools verfügbar sind.

### Operative Effizienz durch Mensch-KI-Zusammenarbeit

Das Human-in-the-Loop-Muster ermöglicht es Organisationen, komplexe Prozesse zu automatisieren und gleichzeitig die menschliche Aufsicht an kritischen Entscheidungspunkten aufrechtzuerhalten. KI-Agenten übernehmen routinemäßige Analysen, Datenerfassung und Entwurfserstellung und eskalieren nur dann an Menschen, wenn Urteilsvermögen oder Genehmigung erforderlich sind. Dieses Kollaborationsmodell bietet Effizienzgewinne durch Automatisierung und bewahrt gleichzeitig Rechenschaftspflicht und Qualitätskontrolle durch menschliche Prüfpunkte.

Organisationen implementieren Workflows wie Spesenabrechnungen (KI prüft Richtlinien und kennzeichnet Probleme, Menschen genehmigen Ausnahmen), Inhaltsmoderation (KI identifiziert potenzielle Probleme, Menschen treffen die endgültigen Entscheidungen) und Kundenanfragen (KI entwirft Antworten, Menschen überprüfen vor dem Senden), die Automatisierungsvorteile mit menschlicher Aufsicht kombinieren.

### Reduzierter IT-Overhead

Die Nutzung der bestehenden Kollaborationsplattform-Infrastruktur eliminiert die Notwendigkeit, zusätzliche Anwendungen bereitzustellen und zu unterstützen. IT-Teams verwalten keine separaten Authentifizierungssysteme, Benutzerbereitstellung oder Helpdesk-Schulungen für den KI-Zugriff. Sicherheits- und Compliance-Kontrollen, die bereits für Kollaborationsplattformen gelten – Datenverlustprävention, Aufbewahrungsrichtlinien, Audit-Protokollierung – werden automatisch auf KI-Konversationen angewendet, ohne dass eine separate Konfiguration erforderlich ist.

Diese Infrastrukturwiederverwendung kommt insbesondere ressourcenbeschränkten Organisationen zugute, bei denen die Bereitstellung und Unterstützung zusätzlicher Unternehmensanwendungen eine erhebliche Belastung darstellt.

### Bereitstellungsflexibilität

Das unabhängige Bereitstellungsmodell ermöglicht es Organisationen, Bot-Funktionen selektiv bereitzustellen – beispielsweise die Teams-Integration für die Zentrale zu aktivieren, während Slack für regionale Büros genutzt wird, oder Web-Chat-Widgets für kundenorientierte Szenarien bereitzustellen, während Teams intern verwendet wird. Verschiedene Kanäle können zu unterschiedlichen Agentenkonfigurationen geleitet werden, was die Segmentierung von Anwendungsfällen oder regulatorische Anforderungen unterstützt, bei denen verschiedene Regionen eine unterschiedliche KI-Handhabung benötigen.

## Implementierungsansatz

Als separater, auf FastAPI basierender Dienst integriert sich die Bot Framework API über plattformspezifische Handler, die Kanalunterschiede verwalten, mit dem Azure Bot Service. Der Dienst verwaltet den Konversationsstatus in MongoDB mit konfigurierbaren Aufbewahrungsrichtlinien und verbindet sich gleichzeitig mit dem NATS-Ereignissystem der Plattform für die bidirektionale Agentenkommunikation. Eingehende Bot-Aktivitäten werden in Plattformereignisse zur Agentenverarbeitung übersetzt, wobei die Antworten zurückgestreamt und für jeden Kanal entsprechend formatiert werden. Das zustandslose Design mit persistentem Konversationsstatus ermöglicht eine horizontale Skalierung basierend auf dem Konversationsvolumen. Die Bereitstellung als unabhängiger Docker-Container unterstützt eine flexible Infrastrukturplatzierung und ein unabhängiges Versionsmanagement von den Kernplattformdiensten. Die Authentifizierung nutzt Azure AD für die Bot-Registrierung, während die Benutzeridentität von Kollaborationsplattformen durch die Plattform-Berechtigungssysteme fließt, wodurch eine konsistente Zugriffssteuerung unabhängig vom Konversationskanal gewährleistet ist.
