---
title: WebSocket API
source_sha: 91092703c1282d3099aacbf3d3fc2be37a9173e530a55aa1367f3d45a1194660
---

# WebSocket API

## Konzept und Zweck

Die WebSocket API, basierend auf FastAPI, bietet bidirektionale Echtzeit-Kommunikationskanäle für Anwendungen, die
sofortiges Feedback während KI-Operationen benötigen. Im Gegensatz zu traditionellen Request-Response-HTTP-Mustern, bei
denen Clients wiederholt auf Updates abfragen müssen, ermöglichen WebSocket-Verbindungen der Plattform, Ereignisse
sofort an Clients zu senden, sobald sie auftreten, und unterstützen so moderne interaktive Benutzererfahrungen.

Diese Fähigkeit adressiert eine grundlegende Herausforderung in KI-Anwendungen: Benutzer müssen in Echtzeit beobachten
können, was autonome Agenten tun, um Vertrauen aufzubauen und das Engagement aufrechtzuerhalten. Ohne
Echtzeit-Transparenz erscheinen langlaufende Agentenoperationen als Black Boxes, was Unsicherheit schafft und das
Vertrauen der Benutzer in KI-gestützte Systeme mindert.

## Grundlegende Designprinzipien

### Echtzeit-Transparenz und Vertrauen

Moderne KI-Anwendungen erfordern reaktionsschnelle Schnittstellen, die kontinuierliches Feedback während der
Agentenausführung liefern. Benutzer erwarten, Agenten-Denkschritte zu beobachten, während sie auftreten, progressives
Streaming von Antwortinhalten zu erhalten, Echtzeit-Statusänderungen zu überwachen und sofortige Benachrichtigungen über
Probleme oder den Abschluss zu erhalten. Diese Transparenz verwandelt undurchsichtige KI-Operationen in beobachtbare,
verständliche Prozesse.

Der geschäftliche Nutzen von Echtzeit-Transparenz geht über die Benutzererfahrung hinaus: Sie schafft Vertrauen in
KI-Systeme, indem sie aufzeigt, wie Agenten zu Schlussfolgerungen gelangen, ermöglicht Benutzern, langlaufende
Operationen zu unterbrechen oder umzulenken, bevor Zeit verschwendet wird, reduziert die wahrgenommene Latenz durch
progressive Offenlegung von Ergebnissen und liefert sofortiges Feedback bei Problemen, anstatt stiller Fehler.

### Brücke zu einer ereignisgesteuerten Architektur

Die WebSocket API dient als Brücke zwischen der internen ereignisgesteuerten Architektur der Plattform und externen
Client-Anwendungen. Alle Plattformoperationen – Agentenausführung, Prozessorchestrierung, Nachrichtenverarbeitung –
erzeugen strukturierte Ereignisse, die über das NATS-Messaging-Backbone fließen. Die WebSocket-Schicht übersetzt diese
internen Ereignisse in vom Client konsumierbare Nachrichten, wodurch eine konsistente Ansicht des Plattformzustands über
alle verbundenen Anwendungen hinweg aufrechterhalten wird.

Diese Architektur stellt sicher, dass mehrere Clients, die dieselben Operationen beobachten, identische Ereignisströme
erhalten, wodurch kollaborative Szenarien unterstützt werden, in denen Teams mit gemeinsamen KI-Assistenten
zusammenarbeiten. Die ereignisbasierte Grundlage ermöglicht auch eine zuverlässige Zustellung: Selbst wenn Verbindungen
vorübergehend fehlschlagen, können Clients verlorene Ereignisse über die Ereignisverlaufs-APIs wiederherstellen.

### Sicherheit und Zugriffskontrolle

Obwohl die WebSocket API Echtzeitzugriff auf Plattformoperationen bietet, wahrt sie strenge Sicherheitsgrenzen.
Verbindungen sind aus Clientsicht schreibgeschützt – Anwendungen empfangen Ereignisse, können aber nicht über den
WebSocket-Kanal veröffentlichen. Dieses Design stellt sicher, dass alle Aktionen, die eine Autorisierungsprüfung
erfordern, über REST APIs erfolgen, wo entsprechende Sicherheitsüberprüfungen stattfinden.

Die Ereignisfilterung basierend auf Benutzerberechtigungen stellt sicher, dass Clients nur Ereignisse für Ressourcen
erhalten, auf die sie zugreifen können: Konversationen, an denen sie teilnehmen, Agenten, die sie verwenden können, und
Prozesse, die sie besitzen oder zu denen sie beitragen. Diese feingranulare Zugriffskontrolle unterstützt
Multi-Tenant-Deployments, bei denen verschiedene Benutzer die Plattforminfrastruktur teilen und gleichzeitig eine
vollständige Datenisolation aufrechterhalten.

## Unterstützte Funktionen

Die API bietet Echtzeit-Transparenz über drei primäre Operationstypen:

**Überwachung der Agentenausführung**: Anwendungen erhalten kontinuierliche Updates, während Agenten Aufgaben ausführen
– Denkprozesse, Tool-Aufrufe, Antwortgenerierung und Abschlussstatus. Das Streaming von Antwort-Chunks ermöglicht die
progressive Anzeige der Agentenausgabe, ähnlich wie Tippindikatoren in Messaging-Anwendungen. Diese Transparenz hilft
Benutzern, die Fähigkeiten und Grenzen von Agenten zu verstehen und so geeignete Vertrauensstufen für verschiedene
Aufgabentypen aufzubauen.

**Konversations-Updates**: Echtzeit-Benachrichtigungen über Änderungen des Konversationsstatus stellen sicher, dass
Benutzer mit kollaborativen Diskussionen synchronisiert bleiben. Anwendungen erfahren sofort, wenn neue Nachrichten
eintreffen, Teilnehmer Konversationen beitreten oder verlassen oder sich Konversationsmetadaten ändern. Dies unterstützt
sowohl Mensch-Mensch- als auch Mensch-KI-Kollaborationsmuster, bei denen mehrere Parteien zur Problemlösung beitragen.

**Prozessstatusverfolgung**: Komplexe mehrstufige Geschäftsprozesse erzeugen Ereignisse, während sie Workflow-Phasen
durchlaufen. Anwendungen können den Prozessstatus anzeigen, aktuelle Schritte hervorheben, den Fortschritt des
Abschlusses anzeigen und Benutzer benachrichtigen, wenn ihre Eingabe erforderlich ist. Diese Transparenz ermöglicht
proaktives Engagement statt reaktiver Benachrichtigung – Benutzer sehen, wie Prozesse voranschreiten, und können
Antworten vorbereiten, bevor sie explizit aufgefordert werden.

## Geschäftlicher Nutzen

### Verbesserte Benutzererfahrung und Engagement

Echtzeit-Feedback verändert die Art und Weise, wie Benutzer mit KI-Systemen interagieren. Anstatt Anfragen zu senden und
ohne Fortschrittsanzeige zu warten, beobachten Benutzer kontinuierliche Aktivitäten, die das Engagement aufrechterhalten
und Vertrauen aufbauen. Diese Transparenz ist besonders wertvoll für komplexe Agentenoperationen, die Minuten oder
Stunden dauern können – Benutzer können den Fortschritt überwachen, verstehen, was der Agent gerade tut, und fundierte
Entscheidungen treffen, ob sie warten oder alternative Ansätze verfolgen sollen. Progressives Antwort-Streaming in
Chat-Schnittstellen fühlt sich natürlicher und ansprechender an als lange Pausen, gefolgt von vollständigen Antworten,
und die Sichtbarkeit des Prozessstatus hilft Benutzern zu verstehen, wo sie sich in mehrstufigen Workflows befinden.

### Operative Effizienz und Kostenmanagement

Echtzeit-Überwachung ermöglicht es Benutzern, unproduktive Operationen frühzeitig zu identifizieren und abzubrechen,
wodurch verschwendete Rechenressourcen und API-Kosten vermieden werden. Wenn Agenten falsche Denkwege einschlagen oder
auf Probleme stoßen, ermöglicht die sofortige Transparenz ein Eingreifen, bevor erhebliche Ressourcen verbraucht werden.
Diese Fähigkeit wird zunehmend wichtiger, wenn Unternehmen KI-Deployments über mehrere Teams und Anwendungsfälle hinweg
skalieren.

Administratoren profitieren von der Echtzeit-Plattformüberwachung – indem sie Agentenauslastungsmuster beobachten,
Leistungsengpässe identifizieren und sofortige Benachrichtigungen über Systemprobleme erhalten. Diese operative
Transparenz unterstützt proaktives Management statt reaktiver Fehlerbehebung.

### Kollaborative KI-Workflows

Die Multi-Client-Unterstützung der WebSocket API ermöglicht Szenarien der Teamzusammenarbeit, bei denen mehrere Benutzer
gemeinsam mit geteilten KI-Assistenten arbeiten. Alle Teilnehmer erhalten identische Ereignisströme, wodurch
sichergestellt wird, dass alle dieselben Agentenverhaltensweisen und Konversationsentwicklungen beobachten. Diese
Fähigkeit unterstützt Anwendungsfälle wie Gruppenentscheidungen mit KI-Unterstützung, Trainingsszenarien, in denen
Experten KI-Interaktionen leiten, und Qualitätsprüfungsprozesse, bei denen Vorgesetzte die Agentenleistung überwachen.

## Implementierungsansatz

Basierend auf den WebSocket-Funktionen von FastAPI integriert sich die API direkt in das NATS JetStream Event Backbone
der Plattform. Persistente Verbindungen verarbeiten Tausende von gleichzeitigen Clients pro Instanz mit minimalem
Ressourcenaufwand. Die Authentifizierung erfolgt über Bearer-Tokens, die gegen organisatorische Identitätsprovider
validiert werden, mit automatischer Verbindungsbeendigung bei Authentifizierungsfehlern. Die Ereignisfilterung wendet
hierarchische Berechtigungsprüfungen vor der Zustellung an, wodurch sichergestellt wird, dass Benutzer nur Ereignisse
für autorisierte Ressourcen erhalten. Die Architektur skaliert horizontal über API-Instanzen hinweg mittels
NATS-basiertem Event-Broadcasting, wodurch eine konsistente Ereigniszustellung gewährleistet wird, unabhängig davon,
welche Instanz eine bestimmte Client-Verbindung bedient. Die typische Latenz bei der Ereigniszustellung liegt unter 50
Millisekunden, was wirklich Echtzeit-Benutzererfahrungen unterstützt.
