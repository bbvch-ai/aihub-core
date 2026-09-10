---
title: Datenaufbewahrungsrichtlinien
source_sha: 3bb00e650b15931284d766a3ca3282471e0816d5f60f3d645bbf6991d46b048d
---

## Strategie zur Datenaufbewahrung

Die Plattform implementiert eine gestufte Aufbewahrungsstrategie:

**Ephemere Daten (automatische Löschung nach 30 Tagen)**: Hochleistungs-Arbeitsspeicher, der in Redis gespeichert ist,
läuft automatisch ab. Ausführungsspezifische Daten bieten ein festes 30-Tage-Fenster für das Debugging. Der
Konversationsspeicher verwendet eine gleitende 30-Tage-Ablaufzeit, die bei jedem Zugriff zurückgesetzt wird.

**Workflow-Ereignisse (doppelte Beschränkungen)**: NATS JetStream verwaltet Workflow-Ereignisse mit sowohl zeitbasierten
(30 Tage) als auch kapazitätsbasierten (10 Millionen Nachrichten) Grenzen. Bei Deployments mit hohem Durchsatz können
Ereignisse vor Ablauf der 30-Tages-Frist gelöscht werden, wenn die Kapazität erreicht ist.

**Permanenter Speicher (manuelles Lifecycle-Management)**: NoSQL-Speicher bewahrt den Konversationsverlauf auf
unbestimmte Zeit ohne automatischen Ablauf auf. Organisationen müssen explizite Daten-Lifecycle-Richtlinien
implementieren, die auf regulatorische Anforderungen und geschäftliche Bedürfnisse abgestimmt sind.

**Operative Implikationen**: Organisationen haben ein 30-Tage-Fenster für die forensische Analyse von
Workflow-Ausführungsdetails. Kritische Ausführungsinformationen sollten vor Erreichen der 30-Tages-Schwelle für eine
langfristige Aufbewahrung im permanenten Speicher abgelegt werden. Compliance-Untersuchungen, die eine
Workflow-Rekonstruktion erfordern, sind auf das verfügbare Aufbewahrungsfenster beschränkt.

**Dagster Betriebs-Logs (separater Aufbewahrungspfad)**: Ausführliche Python-Logger-Einträge (`DEBUG`, `INFO`,
`WARNING`), die von Pipelines und Agents ausgegeben werden, sowie temporäre Framework-interne Ereignisse
(`HANDLED_OUTPUT`, `LOADED_INPUT`, `ENGINE_EVENT`, `ASSET_MATERIALIZATION_PLANNED`, `STEP_OUTPUT`) werden vom
kontinuierlichen Wartungssubsystem der Plattform automatisch bereinigt, um ein unbegrenztes Wachstum von Postgres zu
verhindern. Standard-Aufbewahrungsfenster sind 7 Tage für `DEBUG`, 60 Tage für `INFO`/`WARNING` und 30 Tage für
temporäre Framework-Ereignisse; konfigurierbar pro Deployment über die Umgebungsvariablen
`DAGSTER_*_LOG_RETENTION_DAYS`. Asset Materialisierungen, Schritt-Erfolge/-Fehler und Ausführungsdatensätze werden von
diesem Subsystem **niemals** bereinigt – sie bleiben für die Lebensdauer des Deployments verfügbar, es sei denn, sie
werden explizit gelöscht. Weitere Details finden Sie unter
[Backup und Wiederherstellung](../../3_deployment_guide/4_backup_and_recovery/#continuous-postgres-maintenance).
