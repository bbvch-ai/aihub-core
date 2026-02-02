---
title: Datenaufbewahrungsrichtlinien
source_sha: b3f77f6ae5c02f2fbcdba7587adc9d5dd4817b4d58fd4de8515ff7bcf27860ff
---

## Datenaufbewahrungsstrategie

Die Plattform implementiert eine gestaffelte Aufbewahrungsstrategie:

**Ephemere Daten (automatische Löschung nach 30 Tagen)**: Hochleistungs-Arbeitsspeicher, der in Redis gespeichert ist,
läuft automatisch ab. Ausführungsspezifische Daten bieten ein festes 30-Tage-Fenster für das Debugging. Der
Konversationsspeicher verwendet eine gleitende 30-Tage-Ablauffrist, die sich mit jedem Zugriff zurücksetzt.

**Workflow-Ereignisse (doppelte Einschränkungen)**: NATS JetStream verwaltet Workflow-Ereignisse sowohl mit
zeitbasierten (30 Tage) als auch mit kapazitätsbasierten (10 Millionen Nachrichten) Limits. In
Hochdurchsatz-Bereitstellungen können Ereignisse vor Ablauf der 30-Tage-Frist gelöscht werden, wenn die Kapazität
erreicht ist.

**Permanenter Speicher (manuelles Lifecycle-Management)**: Der NoSQL-Speicher behält den Konversationsverlauf unbegrenzt
ohne automatischen Ablauf bei. Organisationen müssen explizite Daten-Lifecycle-Richtlinien implementieren, die auf
regulatorische Anforderungen und geschäftliche Bedürfnisse abgestimmt sind.

**Betriebliche Auswirkungen**: Organisationen haben ein 30-Tage-Fenster für die forensische Analyse von
Workflow-Ausführungsdetails. Kritische Ausführungsinformationen sollten vor Erreichen der 30-Tage-Schwelle für die
langfristige Aufbewahrung im permanenten Speicher abgelegt werden. Compliance-Untersuchungen, die eine
Workflow-Rekonstruktion erfordern, sind auf das verfügbare Aufbewahrungsfenster beschränkt.
