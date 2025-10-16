---
title: Datenaufbewahrungsrichtlinien
index: 1
source_sha: "bee823f31eacd4342b9a87b2557ef35016a546036bef47a42487ec6b7ec7a4d6"
---

## Datenaufbewahrungsstrategie

Die Plattform implementiert eine mehrstufige Aufbewahrungsstrategie, die betriebliche Effizienz mit Compliance-Verpflichtungen in Einklang bringt:

**Ephemere Daten (automatische Löschung nach 30 Tagen)**: Hochleistungs-Arbeitsspeicher, der in Redis gespeichert ist, läuft automatisch ab. Ausführungsspezifische Daten bieten ein festes 30-Tage-Fenster für das Debugging, während der Konversationsspeicher eine gleitende 30-Tage-Ablaufzeit nutzt, die sich bei jedem Zugriff zurücksetzt.

**Workflow-Ereignisse (Doppelte Einschränkungen)**: NATS JetStream verwaltet Workflow-Ereignisse mit sowohl zeitbasierten (30 Tage) als auch kapazitätsbasierten (10 Millionen Nachrichten) Limits. In Hochdurchsatz-Bereitstellungen können Ereignisse deutlich vor dem 30-Tage-Limit gelöscht werden, wenn die Kapazität erreicht ist.

**Permanenter Speicher (Manuelles Lifecycle-Management)**: NoSQL-Speicher behält den Konversationsverlauf unbegrenzt ohne automatische Ablaufzeit bei. Organisationen müssen explizite Richtlinien für den Datenlebenszyklus implementieren, die auf regulatorische Anforderungen und geschäftliche Bedürfnisse abgestimmt sind.

**Betriebliche Implikationen**: Organisationen haben ein 30-Tage-Fenster für die forensische Analyse von Workflow-Ausführungsdetails. Kritische Ausführungsinformationen sollten vor Erreichen der 30-Tage-Schwelle für die langfristige Aufbewahrung in einem permanenten Speicher persistiert werden. Compliance-Untersuchungen, die eine Workflow-Rekonstruktion erfordern, sind auf das verfügbare Aufbewahrungsfenster beschränkt.
