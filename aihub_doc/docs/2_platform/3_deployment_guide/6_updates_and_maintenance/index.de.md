---
title: Updates & Wartung
source_sha: "2bbfa488a768f7e0213c1c6ec6529d9c1b610302b80cd21f9b38b6b443220198"
---

# Updates und Wartung

## Architektur

Der AI-Hub trennt die Kernplattformkomponenten vom kundenspezifischen Code. Die Kernplattform (dieses Repository) enthält gemeinsame Basiskomponenten wie API, Web, Dagster und Bot. Kunden-Repositories enthalten benutzerdefinierte Agents, Pipelines und Prozesse. Beide verwenden eine unabhängige semantische Versionierung und können separat aktualisiert werden.

Kundencode ist über `pyproject.toml` an eine bestimmte Core-Version gebunden:

```toml
[tool.poetry.dependencies]
aihub-core = { git = "https://github.com/bbvch-ai/aihub-core.git", tag = "v1.2.3" }
```

Das bedeutet, dass Core-Updates die Kunden-Deployments nicht automatisch beeinflussen. Kunden steuern, wann sie neue Core-Versionen übernehmen.

---

## Versionierung

Die Kernplattform verwendet semantische Versionierung:

- Major (X.0.0): Breaking Changes und architektonische Updates
- Minor (0.X.0): Neue Features, abwärtskompatible Änderungen
- Patch (0.0.X): Bugfixes und Sicherheits-Patches

Drei Versions-Tags sind verfügbar:

| Tag | Beschreibung | Stabilität |
| --------- | ------------------------ | --------- |
| `latest` | Letztes stabiles Release | Hoch |
| `nightly` | Letzter Entwicklungs-Build | Mittel |
| `v1.2.3` | Spezifischer Versions-Tag | Höchste |

Kundencode verwendet seine eigenen unabhängigen Versionsnummern.

### Release-Prozess

Wenn ein PR mit einem Versionslabel (`major`, `minor` oder `patch`) in `main` gemergt wird, berechnet CI/CD die neue Version und erstellt einen Git-Tag. Dies löst Komponenten-Builds für betroffene Services aus. Docker-Images werden unter `ghcr.io/bbvch-ai/aihub-core/*` mit dem Versions-Tag veröffentlicht. Ein Changelog wird automatisch generiert.

Beispiel Core-Images:

```
ghcr.io/bbvch-ai/aihub-core/api:v1.2.3
ghcr.io/bbvch-ai/aihub-core/dagster:v1.2.3
ghcr.io/bbvch-ai/aihub-core/web:v1.2.3
```

Kundencode folgt dem gleichen CI/CD-Muster:

```
ghcr.io/bbvch-ai/aihub-<customer>/agent:v1.2.3
ghcr.io/bbvch-ai/aihub-<customer>/pipeline:v1.2.3
```

---

## Updates

### Core-Plattform-Updates

Abwärtskompatible Core-Updates (Patch- und Minor-Versionen) können durch Aktualisieren der Image-Tags in `docker-compose.yml`, Herunterladen neuer Images und Neustarten der Services deployed werden. Der Kundencode läuft dabei unverändert weiter.

Major Core-Updates mit Breaking Changes erfordern koordinierte Updates. Der Kundencode muss aktualisiert werden, um mit der neuen Core-Version zu funktionieren. Sowohl Core- als auch Kundencode werden während eines Wartungsfensters gemeinsam aktualisiert.

### Kundencode-Updates

Kundencode kann unabhängig aktualisiert werden, solange die Core-Version-Pin unverändert bleibt. Aktualisieren Sie die Kunden-Image-Tags in `docker-compose.yml`, laden Sie die neuen Images herunter und starten Sie die Kunden-Services neu.

Wenn Kundencode eine neue Core-Version übernimmt, aktualisieren Sie die Core-Version-Pin in `pyproject.toml`, erstellen Sie die Kunden-Images neu und deployen Sie dann sowohl Core- als auch Kunden-Updates zusammen.

---

## Rollbacks

### VM-Snapshots

VM-Snapshots erfassen den gesamten Systemzustand. Ein Rollback stellt die komplette VM von einem Pre-Update-Snapshot wieder her und versetzt alle Services gleichzeitig in ihren vorherigen Zustand zurück.

### Versions-Tags

Wenn Daten mit der vorherigen Version kompatibel bleiben, führen Sie ein Rollback durch, indem Sie die Image-Tags in `docker-compose.yml` auf die vorherigen Versionen zurücksetzen, diese Images herunterladen und die Services neu starten.

Core- und Kundencode können unabhängig voneinander zurückgesetzt werden, wenn sie separat aktualisiert wurden. Wenn beide zusammen aktualisiert wurden, setzen Sie zuerst den Core zurück, dann den Kundencode.

---

## Kompatibilität

Kundencode ist an spezifische Core-Versionen gebunden, um Stabilität zu gewährleisten. Eine Kompatibilitätsmatrix verfolgt, welche Kundenversionen mit welchen Core-Versionen funktionieren:

| Kundenversion | Core-Version | Status | Hinweise |
| ---------------- | ------------ | --------- | ------------------ |
| v1.0.0 | v0.1.2 | Legacy | End of Life |
| v1.1.0 | v1.2.3 | Supported | Aktuelle Produktion |
| v1.2.0 | v1.2.3 | Supported | Neueste Features |
| v2.0.0 | v2.3.4 | Testing | Nächstes Major Release |

Staging-Umgebungen sollten der Produktionsinfrastruktur entsprechen und repräsentative Datensätze für die Kompatibilitätstests vor Produktions-Updates verwenden.

---

## Monitoring

Der Observability Stack umfasst Phoenix für AI-spezifisches Tracing, OpenTelemetry für verteiltes Tracing und optional SigNoz Cloud für externe Metriken und Logs. Überwachen Sie Core-Services (API, Web, Dagster) und Kunden-Services (Agents, Pipelines, Prozesse) während und nach Updates.

---

## Verwandte Dokumentation

- [Deployment-Optionen](../1_deployment_options/) - Pro-Instanz-Architektur
- [Multi-Tenancy](../../15_multi_tenancy/) - Logische Trennung innerhalb von Instanzen
- [Backup und Recovery](../4_backup_and_recovery/) - Backup-Strategien
- [Core-Komponenten](../../2_architecture/1_core_components/) - Komponentenabhängigkeiten
