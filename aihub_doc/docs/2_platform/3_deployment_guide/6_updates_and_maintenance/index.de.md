---
title: Updates & Wartung
source_sha: baf13f382cb9c8cc382828c8dbf9d23a6301964e77d8a95afc111c37caa84de8
---

# Updates und Wartung

## Architektur

Der AI-Hub trennt Kernplattformkomponenten von kundenspezifischem Code. Die Kernplattform (dieses Repository) enthält
gemeinsame Basiskomponenten wie API, Web, Dagster und Bot. Kunden-Repositories enthalten benutzerdefinierte Agents,
Pipelines und Prozesse. Beide verwenden eine unabhängige semantische Versionierung und können separat aktualisiert
werden.

Kundenspezifischer Code fixiert sich auf eine bestimmte Core-Version über `pyproject.toml`:

```toml
[tool.poetry.dependencies]
aihub-core = { git = "https://github.com/bbvch-ai/aihub-core.git", tag = "v1.2.3" }
```

Das bedeutet, dass Core-Updates Kunden-Deployments nicht automatisch beeinflussen. Kunden steuern, wann sie neue
Core-Versionen übernehmen.

---

## Versionierung

Die Kernplattform verwendet semantische Versionierung:

- Major (X.0.0): Breaking Changes und architektonische Updates
- Minor (0.X.0): Neue Features, abwärtskompatible Änderungen
- Patch (0.0.X): Bugfixes und Sicherheitsupdates

Drei Versions-Tags sind verfügbar:

| Tag       | Beschreibung                | Stabilität |
| --------- | --------------------------- | ---------- |
| `latest`  | Neueste stabile Version     | Hoch       |
| `nightly` | Neuester Entwicklungs-Build | Mittel     |
| `v1.2.3`  | Spezifischer Versions-Tag   | Höchste    |

Kundenspezifischer Code verwendet eigene, unabhängige Versionsnummern.

### Release-Prozess

Wenn ein PR in `main` mit einem Versionslabel (`major`, `minor` oder `patch`) gemergt wird, berechnet CI/CD die neue
Version und erstellt einen Git-Tag. Dies löst Komponenten-Builds für betroffene Services aus. Docker-Images werden unter
`ghcr.io/bbvch-ai/aihub-core/*` mit dem Versions-Tag veröffentlicht. Ein Changelog wird automatisch generiert.

Beispiel Core-Images:

```
ghcr.io/bbvch-ai/aihub-core/api:v1.2.3
ghcr.io/bbvch-ai/aihub-core/dagster:v1.2.3
ghcr.io/bbvch-ai/aihub-core/web:v1.2.3
```

Kundenspezifischer Code folgt dem gleichen CI/CD-Muster:

```
ghcr.io/bbvch-ai/aihub-<customer>/agent:v1.2.3
ghcr.io/bbvch-ai/aihub-<customer>/pipeline:v1.2.3
```

---

## Updates

### Core-Plattform-Updates

Abwärtskompatible Core-Updates (Patch- und Minor-Versionen) können durch Aktualisierung der Image-Tags in
`docker-compose.yml`, das Pulling neuer Images und das Neustarten der Services deployed werden. Kundenspezifischer Code
läuft unverändert weiter.

Major Core-Updates mit Breaking Changes erfordern koordinierte Updates. Kundenspezifischer Code muss aktualisiert
werden, um mit der neuen Core-Version zu funktionieren. Sowohl Core- als auch kundenspezifischer Code werden zusammen
während eines Wartungsfensters aktualisiert.

### Updates des kundenspezifischen Codes

Kundenspezifischer Code kann unabhängig aktualisiert werden, wenn der Core-Versions-Pin unverändert bleibt.
Aktualisieren Sie die Kunden-Image-Tags in `docker-compose.yml`, pullen Sie die neuen Images und starten Sie die
Kunden-Services neu.

Wenn kundenspezifischer Code eine neue Core-Version übernimmt, aktualisieren Sie den Core-Versions-Pin in
`pyproject.toml`, bauen Sie die Kunden-Images neu und deployen Sie dann sowohl Core- als auch Kunden-Updates zusammen.

---

## Rollbacks

### VM-Snapshots

VM-Snapshots erfassen den gesamten Systemzustand. Ein Rollback stellt die komplette VM von einem Pre-Update-Snapshot
wieder her, wodurch alle Services gleichzeitig in ihren vorherigen Zustand zurückversetzt werden.

### Versions-Tags

Wenn die Daten mit der vorherigen Version kompatibel bleiben, führen Sie ein Rollback durch, indem Sie die Image-Tags in
`docker-compose.yml` auf die vorherigen Versionen zurücksetzen, diese Images pullen und die Services neu starten.

Core- und kundenspezifischer Code können unabhängig zurückgesetzt werden, wenn sie separat aktualisiert wurden. Wenn
beide zusammen aktualisiert wurden, setzen Sie zuerst den Core zurück, dann den kundenspezifischen Code.

---

## Kompatibilität

Kundenspezifischer Code fixiert sich auf spezifische Core-Versionen, um die Stabilität zu gewährleisten. Eine
Kompatibilitätsmatrix verfolgt, welche Kundenversionen mit welchen Core-Versionen funktionieren:

| Kundenversion | Core-Version | Status      | Anmerkungen           |
| ------------- | ------------ | ----------- | --------------------- |
| v1.0.0        | v0.1.2       | Legacy      | End-of-Life           |
| v1.1.0        | v1.2.3       | Unterstützt | Aktuelle Produktion   |
| v1.2.0        | v1.2.3       | Unterstützt | Neueste Features      |
| v2.0.0        | v2.3.4       | Testphase   | Nächste Major-Version |

Staging-Umgebungen sollten der Produktionsinfrastruktur entsprechen und repräsentative Datensätze zur
Kompatibilitätsprüfung vor Produktions-Updates verwenden.

---

## Monitoring

Der Observability Stack beinhaltet Phoenix für KI-spezifisches Tracing, OpenTelemetry für verteiltes Tracing und
optional SigNoz Cloud für externe Metriken und Logs. Überwachen Sie Core-Services (API, Web, Dagster) und
Kunden-Services (Agents, Pipelines, Prozesse) während und nach Updates.

---

## Verwandte Dokumentation

- [Deployment-Optionen](../1_deployment_options/) – Pro-Tenant-Architektur
- [Backup und Wiederherstellung](../4_backup_and_recovery/) – Backup-Strategien
- [Core-Komponenten](../../2_architecture/1_core_components/) – Komponenten-Abhängigkeiten
