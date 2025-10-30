---
title: Datenaufbewahrungsrichtlinien
source_sha: 01a4ef39e7c9f58e8cc49cd77f20e15a6fab0c2c17e80df92b71451fd6a8244d
---

## Datenaufbewahrungsstrategie

Die Plattform implementiert eine gestufte Aufbewahrungsstrategie:

**Ephemere Daten (automatische Löschung nach 30 Tagen)**: Der in Redis gespeicherte Hochleistungs-Arbeitsspeicher läuft
automatisch ab. Ausführungsspezifische Daten bieten ein festes 30-Tage-Fenster für das Debugging. Konversationsspeicher
nutzt einen gleitenden 30-Tage-Ablauf, der bei jedem Zugriff zurückgesetzt wird.

**Workflow-Ereignisse (doppelte Beschränkungen)**: NATS JetStream verwaltet Workflow-Ereignisse mit zeitbasierten (30
Tage) und kapazitätsbasierten (10 Millionen Nachrichten) Limits. In Bereitstellungen mit hohem Durchsatz können
Ereignisse vor Ablauf der 30-Tage-Frist gelöscht werden, wenn die Kapazitätsgrenze erreicht ist.

**Permanenter Speicher (manuelles Lebenszyklusmanagement)**: NoSQL-Speicher bewahrt den Konversationsverlauf unbegrenzt
ohne automatischen Ablauf auf. Organisationen müssen explizite Datenlebenszyklusrichtlinien implementieren, die auf
regulatorische Anforderungen und geschäftliche Bedürfnisse abgestimmt sind.

**Operative Auswirkungen**: Organisationen haben ein 30-Tage-Fenster für die forensische Analyse von
Workflow-Ausführungsdetails. Kritische Ausführungsinformationen sollten vor Erreichen der 30-Tage-Schwelle für eine
langfristige Aufbewahrung in den permanenten Speicher persistiert werden. Compliance-Untersuchungen, die eine
Workflow-Rekonstruktion erfordern, sind auf das verfügbare Aufbewahrungsfenster beschränkt.
