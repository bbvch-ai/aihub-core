---
title: WebSocket-API
index: 3
source_sha: "8a5d88b780b6c7559c613f9a5be9854ceb38787e32035c993257cd852abcb590"
---

# WebSocket-API

## Konzept und Zweck

Die WebSocket-API, die auf FastAPI basiert, bietet bidirektionale Echtzeit-Kommunikationskanäle für Anwendungen, die während KI-Operationen sofortiges Feedback benötigen. Im Gegensatz zu herkömmlichen Anforderungs-Antwort-HTTP-Mustern, bei denen Clients wiederholt auf Updates abfragen müssen, ermöglichen WebSocket-Verbindungen der Plattform, Ereignisse sofort an Clients zu senden, sobald sie auftreten, und unterstützen so moderne interaktive Benutzererfahrungen.

Diese Fähigkeit begegnet einer grundlegenden Herausforderung in KI-Anwendungen: Benutzer müssen in Echtzeit beobachten können, was autonome Agenten tun, um Vertrauen aufzubauen und Engagement aufrechtzuerhalten. Ohne Echtzeit-Sichtbarkeit erscheinen langwierige Agentenoperationen als Black Boxes, was Unsicherheit schafft und das Vertrauen der Benutzer in KI-gestützte Systeme mindert.

## Kernprinzipien des Designs

### Echtzeit-Transparenz und Vertrauen

Moderne KI-Anwendungen erfordern reaktionsschnelle Schnittstellen, die während der Agentenausführung kontinuierliches Feedback liefern. Benutzer erwarten, die Argumentationsschritte des Agenten zu beobachten, sobald sie auftreten, progressives Streaming von Antwortinhalten zu erhalten, Echtzeit-Statusänderungen zu überwachen und sofortige Benachrichtigungen über Probleme oder den Abschluss zu erhalten. Diese Transparenz verwandelt undurchsichtige KI-Operationen in beobachtbare, verständliche Prozesse.

Der geschäftliche Nutzen der Echtzeit-Sichtbarkeit geht über die Benutzererfahrung hinaus: Sie schafft Vertrauen in KI-Systeme, indem sie zeigt, wie Agenten zu Schlussfolgerungen gelangen, ermöglicht es Benutzern, langwierige Operationen zu unterbrechen oder umzuleiten, bevor Zeit verschwendet wird, reduziert die wahrgenommene Latenz durch progressive Offenlegung von Ergebnissen und bietet sofortiges Feedback bei Problemen statt stiller Fehler.

### Brücke zur ereignisgesteuerten Architektur

Die WebSocket-API dient als Brücke zwischen der internen ereignisgesteuerten Architektur der Plattform und externen Client-Anwendungen. Alle Plattformoperationen – Agentenausführung, Prozessorchestrierung, Nachrichtenverarbeitung – erzeugen strukturierte Ereignisse, die über das NATS-Messaging-Backbone fließen. Die WebSocket-Schicht übersetzt diese internen Ereignisse in client-konsumierbare Nachrichten und hält so eine konsistente Sicht auf den Plattformstatus über alle verbundenen Anwendungen hinweg aufrecht.

Diese Architektur stellt sicher, dass mehrere Clients, die dieselben Operationen beobachten, identische Ereignisströme erhalten, was kollaborative Szenarien unterstützt, in denen Teams mit gemeinsamen KI-Assistenten zusammenarbeiten. Das ereignisgesteuerte Fundament ermöglicht auch eine zuverlässige Zustellung: selbst wenn Verbindungen vorübergehend fehlschlagen, können Clients verlorene Ereignisse über die Ereignisverlaufs-APIs wiederherstellen.

### Sicherheit und Zugriffskontrolle

Obwohl die WebSocket-API Echtzeitzugriff auf Plattformoperationen bietet, wahrt sie strenge Sicherheitsgrenzen. Verbindungen sind aus Clientsicht schreibgeschützt – Anwendungen empfangen Ereignisse, können aber nicht über den WebSocket-Kanal veröffentlichen. Dieses Design stellt sicher, dass alle Aktionen, die eine Autorisierungsvalidierung erfordern, über REST-APIs erfolgen, wo entsprechende Sicherheitsprüfungen durchgeführt werden.

Die Ereignisfilterung basierend auf Benutzerberechtigungen stellt sicher, dass Clients nur Ereignisse für Ressourcen erhalten, auf die sie zugreifen dürfen: Gespräche, an denen sie teilnehmen, Agenten, die sie verwenden können, und Prozesse, die sie besitzen oder zu denen sie beitragen. Diese feingranulare Zugriffskontrolle unterstützt Multi-Tenant-Bereitstellungen, bei denen verschiedene Benutzer die Plattforminfrastruktur teilen, während eine vollständige Datenisolation aufrechterhalten wird.

## Unterstützte Funktionen

Die API bietet Echtzeit-Sichtbarkeit über drei primäre Operationstypen hinweg:

**Agenten-Ausführungsüberwachung**: Anwendungen erhalten kontinuierliche Updates, während Agenten Aufgaben ausführen – Argumentationsschritte, Tool-Aufrufe, Antwortgenerierung und Abschlussstatus. Das Streaming von Antwort-Chunks ermöglicht die progressive Anzeige der Agentenausgabe, ähnlich wie Tippindikatoren in Messaging-Anwendungen. Diese Sichtbarkeit hilft Benutzern, die Fähigkeiten und Einschränkungen des Agenten zu verstehen und angemessene Vertrauensstufen für verschiedene Aufgabentypen aufzubauen.

**Konversations-Updates**: Die Echtzeit-Benachrichtigung über Änderungen des Konversationsstatus stellt sicher, dass Benutzer bei kollaborativen Diskussionen synchronisiert bleiben. Anwendungen erfahren sofort, wenn neue Nachrichten eintreffen, Teilnehmer Gesprächen beitreten oder diese verlassen oder sich Metadaten von Konversationen ändern. Dies unterstützt sowohl Mensch-Mensch- als auch Mensch-KI-Kollaborationsmuster, bei denen mehrere Parteien zur Problemlösung beitragen.

**Prozessstatusverfolgung**: Komplexe mehrstufige Geschäftsprozesse generieren Ereignisse, während sie die Workflow-Phasen durchlaufen. Anwendungen können den Prozessstatus anzeigen, aktuelle Schritte hervorheben, den Fortschritt des Abschlusses angeben und Benutzer benachrichtigen, wenn ihre Eingabe erforderlich ist. Diese Sichtbarkeit ermöglicht proaktives Engagement anstatt reaktiver Benachrichtigung – Benutzer sehen Prozesse voranschreiten und können Antworten vorbereiten, bevor sie explizit dazu aufgefordert werden.

## Geschäftswert

### Verbesserte Benutzererfahrung und Engagement

Echtzeit-Feedback verändert die Art und Weise, wie Benutzer mit KI-Systemen interagieren. Anstatt Anfragen zu senden und ohne Fortschrittsanzeige zu warten, beobachten Benutzer kontinuierliche Aktivitäten, die das Engagement aufrechterhalten und Vertrauen aufbauen. Diese Transparenz ist besonders wertvoll für komplexe Agentenoperationen, die Minuten oder Stunden dauern können – Benutzer können den Fortschritt überwachen, verstehen, was der Agent gerade tut, und fundierte Entscheidungen treffen, ob sie warten oder alternative Ansätze verfolgen. Progressives Antwort-Streaming in Chat-Oberflächen fühlt sich natürlicher und ansprechender an als lange Pausen, gefolgt von vollständigen Antworten, und die Sichtbarkeit des Prozessstatus hilft Benutzern zu verstehen, wo sie sich in mehrstufigen Workflows befinden.

### Betriebliche Effizienz und Kostenmanagement

Die Echtzeitüberwachung ermöglicht es Benutzern, unproduktive Operationen frühzeitig zu identifizieren und abzubrechen, wodurch verschwendete Rechenressourcen und API-Kosten vermieden werden. Wenn Agenten falsche Argumentationspfade verfolgen oder auf Probleme stoßen, ermöglicht eine sofortige Sichtbarkeit ein Eingreifen, bevor erhebliche Ressourcen verbraucht werden. Diese Fähigkeit wird immer wichtiger, da Unternehmen KI-Bereitstellungen über mehrere Teams und Anwendungsfälle hinweg skalieren.

Administratoren profitieren von der Echtzeit-Plattformüberwachung – sie beobachten Agenten-Auslastungsmuster, identifizieren Leistungsengpässe und erhalten sofortige Benachrichtigungen über Systemprobleme. Diese betriebliche Sichtbarkeit unterstützt proaktives Management statt reaktiver Fehlerbehebung.

### Kollaborative KI-Workflows

Die Multi-Client-Unterstützung der WebSocket-API ermöglicht Szenarien der Teamzusammenarbeit, bei denen mehrere Benutzer gemeinsam mit geteilten KI-Assistenten arbeiten. Alle Teilnehmer erhalten identische Ereignisströme, wodurch sichergestellt wird, dass jeder die gleichen Agentenverhaltensweisen und Konversationsentwicklungen beobachtet. Diese Funktion unterstützt Anwendungsfälle wie Gruppenentscheidungen mit KI-Unterstützung, Trainingsszenarien, in denen Experten KI-Interaktionen leiten, und Qualitätsprüfungsprozesse, bei denen Vorgesetzte die Agentenleistung überwachen.

## Implementierungsansatz

Aufbauend auf den WebSocket-Funktionen von FastAPI integriert sich die API direkt in das NATS JetStream-Ereignis-Backbone der Plattform. Persistente Verbindungen verarbeiten Tausende gleichzeitiger Clients pro Instanz mit minimalem Ressourcen-Overhead. Die Authentifizierung erfolgt über Bearer-Token, die gegen organisationseigene Identitätsanbieter validiert werden, mit automatischer Verbindungsbeendigung bei Authentifizierungsfehlern. Die Ereignisfilterung wendet hierarchische Berechtigungsprüfungen vor der Zustellung an, um sicherzustellen, dass Benutzer nur Ereignisse für autorisierte Ressourcen erhalten. Die Architektur skaliert horizontal über API-Instanzen hinweg mithilfe von NATS-basiertem Event-Broadcasting und gewährleistet eine konsistente Ereigniszustellung, unabhängig davon, welche Instanz eine bestimmte Client-Verbindung bedient. Die typische Latenz bei der Ereigniszustellung bleibt unter 50 Millisekunden und unterstützt somit echte Echtzeit-Benutzererfahrungen.
