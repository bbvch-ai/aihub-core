```markdown
---
title: WebSocket API
source_sha: "f727dc9e6f27470828842fb6dc493dac5923c6c0e644dd64a1552adc2ebb8f29"
---

# WebSocket API

## Konzept und Zweck

Die WebSocket API, basierend auf FastAPI, bietet bidirektionale Echtzeit-Kommunikationskanäle für Anwendungen, die sofortiges Feedback während KI-Operationen benötigen. Im Gegensatz zu traditionellen Request-Response-HTTP-Mustern, bei denen Clients wiederholt auf Updates prüfen müssen, ermöglichen WebSocket-Verbindungen der Plattform, Ereignisse sofort an Clients zu pushen, sobald diese auftreten, und unterstützen so moderne interaktive Benutzererlebnisse.

Diese Fähigkeit adressiert eine grundlegende Herausforderung in KI-Anwendungen: Benutzer müssen in Echtzeit beobachten können, was autonome Agents tun, um Vertrauen aufzubauen und die Interaktion aufrechtzuerhalten. Ohne Echtzeit-Transparenz erscheinen langlaufende Agent-Operationen als Black Boxes, was Unsicherheit erzeugt und das Vertrauen der Benutzer in KI-gestützte Systeme mindert.

## Grundlegende Designprinzipien

### Echtzeit-Transparenz und Vertrauen

Moderne KI-Anwendungen erfordern reaktionsfähige Schnittstellen, die kontinuierliches Feedback während der Agent-Ausführung bieten. Benutzer erwarten, die Argumentationsschritte des Agents zu beobachten, während sie stattfinden, ein progressives Streaming von Antwortinhalten zu erhalten, Echtzeit-Statusänderungen zu überwachen und sofortige Benachrichtigungen über Probleme oder den Abschluss zu erhalten. Diese Transparenz verwandelt undurchsichtige KI-Operationen in beobachtbare, verständliche Prozesse.

Der geschäftliche Nutzen der Echtzeit-Transparenz geht über die Benutzererfahrung hinaus: Sie schafft Vertrauen in KI-Systeme, indem sie zeigt, wie Agents zu Schlussfolgerungen gelangen, ermöglicht Benutzern, langlaufende Operationen zu unterbrechen oder umzuleiten, bevor Zeit verschwendet wird, reduziert die wahrgenommene Latenz durch progressive Offenlegung von Ergebnissen und bietet sofortiges Feedback bei auftretenden Problemen, anstatt stillschweigender Fehler.

### Brücke zur ereignisgesteuerten Architektur

Die WebSocket API dient als Brücke zwischen der internen ereignisgesteuerten Architektur der Plattform und externen Client-Anwendungen. Alle Plattformoperationen – Agent-Ausführung, Prozess-Orchestrierung, Nachrichtenverarbeitung – erzeugen strukturierte Ereignisse, die über den NATS-Messaging-Backbone fließen. Die WebSocket-Schicht übersetzt diese internen Ereignisse in Client-konsumierbare Nachrichten und erhält so eine konsistente Sicht auf den Plattformstatus über alle verbundenen Anwendungen hinweg.

Diese Architektur stellt sicher, dass mehrere Clients, die dieselben Operationen beobachten, identische Ereignisströme erhalten, was kollaborative Szenarien unterstützt, in denen Teams mit gemeinsamen KI-Assistenten zusammenarbeiten. Die ereignisgesteuerte Grundlage ermöglicht auch eine zuverlässige Zustellung: Selbst wenn Verbindungen vorübergehend fehlschlagen, können Clients verlorene Ereignisse über die Ereignisverlaufs-APIs wiederherstellen.

### Sicherheit und Zugriffskontrolle

Obwohl die WebSocket API Echtzeitzugriff auf Plattformoperationen bietet, behält sie strenge Sicherheitsgrenzen bei. Verbindungen sind aus Clientsicht nur lesbar – Anwendungen empfangen Ereignisse, können aber nicht über den WebSocket-Kanal veröffentlichen. Dieses Design stellt sicher, dass alle Aktionen, die eine Autorisierungsprüfung erfordern, über REST APIs erfolgen, wo entsprechende Sicherheitsüberprüfungen stattfinden.

Die Ereignisfilterung basierend auf Benutzerberechtigungen stellt sicher, dass Clients nur Ereignisse für Ressourcen erhalten, auf die sie zugreifen können: Konversationen, an denen sie teilnehmen, Agents, die sie nutzen können, und Prozesse, die sie besitzen oder zu denen sie beitragen. Diese feingranulare Zugriffskontrolle unterstützt Multi-Tenant-Deployments, bei denen verschiedene Benutzer die Plattforminfrastruktur gemeinsam nutzen, aber eine vollständige Datenisolation beibehalten wird.

## Unterstützte Funktionen

Die API bietet Echtzeit-Transparenz über drei primäre Operationstypen hinweg:

**Agent-Ausführungsüberwachung**: Anwendungen erhalten kontinuierliche Updates, während Agents Aufgaben ausführen – Argumentationsschritte, Tool-Aufrufe, Antwortgenerierung und Abschlussstatus. Das Streaming von Antwortfragmenten ermöglicht eine progressive Anzeige der Agent-Ausgabe, ähnlich den Tippindikatoren in Messaging-Anwendungen. Diese Transparenz hilft Benutzern, die Fähigkeiten und Einschränkungen des Agents zu verstehen und so angemessene Vertrauensniveaus für verschiedene Aufgabentypen aufzubauen.

**Konversations-Updates**: Echtzeit-Benachrichtigungen über Änderungen des Konversationsstatus stellen sicher, dass Benutzer mit kollaborativen Diskussionen synchronisiert bleiben. Anwendungen erfahren sofort, wenn neue Nachrichten eintreffen, Teilnehmer Konversationen beitreten oder verlassen oder sich Metadaten der Konversation ändern. Dies unterstützt sowohl Mensch-Mensch- als auch Mensch-KI-Kollaborationsmuster, bei denen mehrere Parteien zur Problemlösung beitragen.

**Prozessstatus-Verfolgung**: Komplexe mehrstufige Geschäftsprozesse erzeugen Ereignisse, während sie die Workflow-Phasen durchlaufen. Anwendungen können den Prozessstatus anzeigen, aktuelle Schritte hervorheben, den Fortschritt der Fertigstellung angeben und Benutzer benachrichtigen, wenn ihre Eingabe erforderlich ist. Diese Transparenz ermöglicht proaktives Engagement statt reaktiver Benachrichtigung – Benutzer sehen Prozesse voranschreiten und können Antworten vorbereiten, bevor sie explizit dazu aufgefordert werden.

## Geschäftlicher Nutzen

### Verbesserte Benutzererfahrung und Engagement

Echtzeit-Feedback verändert die Art und Weise, wie Benutzer mit KI-Systemen interagieren. Anstatt Anfragen zu senden und ohne Fortschrittsanzeige zu warten, beobachten Benutzer eine kontinuierliche Aktivität, die das Engagement aufrechterhält und Vertrauen aufbaut. Diese Transparenz ist besonders wertvoll für komplexe Agent-Operationen, die Minuten oder Stunden dauern können – Benutzer können den Fortschritt überwachen, verstehen, was der Agent gerade tut, und fundierte Entscheidungen treffen, ob sie warten oder alternative Ansätze verfolgen sollen. Progressives Antwort-Streaming in Chat-Oberflächen fühlt sich natürlicher und ansprechender an als lange Pausen, gefolgt von vollständigen Antworten, und die Sichtbarkeit des Prozessstatus hilft Benutzern zu verstehen, wo sie sich in mehrstufigen Workflows befinden.

### Operative Effizienz und Kostenmanagement

Echtzeit-Monitoring ermöglicht es Benutzern, unproduktive Operationen frühzeitig zu identifizieren und abzubrechen, wodurch verschwendete Rechenressourcen und API-Kosten vermieden werden. Wenn Agents falsche Argumentationswege verfolgen oder auf Probleme stoßen, ermöglicht die sofortige Transparenz ein Eingreifen, bevor erhebliche Ressourcen verbraucht werden. Diese Fähigkeit wird zunehmend wichtiger, da Organisationen KI-Deployments über mehrere Teams und Anwendungsfälle hinweg skalieren.

Administratoren profitieren von Echtzeit-Plattform-Monitoring – sie beobachten Agent-Auslastungsmuster, identifizieren Leistungsengpässe und erhalten sofortige Benachrichtigungen über Systemprobleme. Diese operative Transparenz unterstützt proaktives Management statt reaktiver Fehlerbehebung.

### Kollaborative KI-Workflows

Die Multi-Client-Unterstützung der WebSocket API ermöglicht Szenarien der Teamzusammenarbeit, bei denen mehrere Benutzer gemeinsam mit geteilten KI-Assistenten arbeiten. Alle Teilnehmer erhalten identische Ereignisströme, wodurch sichergestellt wird, dass alle die gleichen Agent-Verhaltensweisen und Konversationsentwicklungen beobachten. Diese Fähigkeit unterstützt Anwendungsfälle wie Gruppenentscheidungen mit KI-Unterstützung, Trainingsszenarien, in denen Experten KI-Interaktionen leiten, und Qualitätssicherungsprozesse, bei denen Vorgesetzte die Agent-Performance überwachen.

## Implementierungsansatz

Basierend auf den WebSocket-Funktionen von FastAPI integriert sich die API direkt in den NATS JetStream Event Backbone der Plattform. Persistente Verbindungen verwalten Tausende von gleichzeitigen Clients pro Instanz mit minimalem Ressourcen-Overhead. Die Authentifizierung erfolgt über Bearer-Tokens, die gegen organisatorische Identity Provider validiert werden, mit automatischer Verbindungsbeendigung bei Authentifizierungsfehlern. Die Ereignisfilterung wendet hierarchische Berechtigungsprüfungen vor der Zustellung an, wodurch sichergestellt wird, dass Benutzer nur Ereignisse für autorisierte Ressourcen erhalten. Die Architektur skaliert horizontal über API-Instanzen mittels NATS-basiertem Ereignis-Broadcasting, wodurch eine konsistente Ereigniszustellung gewährleistet wird, unabhängig davon, welche Instanz eine bestimmte Client-Verbindung bedient. Die typische Ereigniszustellungs-Latenz bleibt unter 50 Millisekunden und unterstützt somit wahrhaftige Echtzeit-Benutzererlebnisse.
```
