---
title: 'Updates & Wartung'
source_sha: "636f7635d30a115f15a40350307eb1f9da344aedf30efdd17827b03036acd5b2"
---

# Updates und Wartung

## Architektur

Die AI-Hub trennt zentrale Plattformkomponenten von kundenspezifischem Code. Die Kernplattform (dieses Repository) enthält gemeinsam genutzte Basiskomponenten wie API, Web, Dagster und Bot. Kunden-Repositories enthalten benutzerdefinierte Agents, Pipelines und Prozesse. Beide verwenden unabhängige semantische Versionierung und können separat aktualisiert werden.

Kundencode fixiert sich über `pyproject.toml` auf eine bestimmte Core-Version:

```toml
[tool.poetry.dependencies]
aihub-core = { git = "https://github.com/bbvch-ai/aihub-core.git", tag = "v1.2.3" }
```

Das bedeutet, dass Core-Updates Kunden-Deployments nicht automatisch beeinflussen. Kunden steuern, wann sie neue Core-Versionen übernehmen.

---

## Versionierung

Die Kernplattform verwendet semantische Versionierung:

- Major (X.0.0): Breaking Changes und architektonische Updates
- Minor (0.X.0): Neue Funktionen, abwärtskompatible Änderungen
- Patch (0.0.X): Bugfixes und Sicherheitspatches

Drei Versionstags sind verfügbar:

| Tag | Beschreibung | Stabilität |
|-----|-------------|-----------|
| `latest` | Neueste stabile Version | Hoch |
| `nightly` | Neuester Entwicklungsbuild | Mittel |
| `v1.2.3` | Spezifischer Versionstag | Höchste |

Kundencode verwendet seine eigenen, unabhängigen Versionsnummern.

### Release-Prozess

Wenn ein PR mit einem Versionslabel (`major`, `minor` oder `patch`) in `main` gemergt wird, berechnet CI/CD die neue Version und erstellt einen Git-Tag. Dies löst Komponenten-Builds für betroffene Services aus. Docker-Images werden unter `ghcr.io/bbvch-ai/aihub-core/*` mit dem Versionstag veröffentlicht. Ein Changelog wird automatisch generiert.

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

Abwärtskompatible Core-Updates (Patch- und Minor-Versionen) können durch Aktualisieren der Image-Tags in `docker-compose.yml`, Herunterladen neuer Images und Neustarten der Services bereitgestellt werden. Kundencode läuft unverändert weiter.

Major Core-Updates mit Breaking Changes erfordern koordinierte Updates. Kundencode muss aktualisiert werden, um mit der neuen Core-Version zu funktionieren. Sowohl Core- als auch Kundencode werden während eines Wartungsfensters gemeinsam aktualisiert.

### Kundencode-Updates

Kundencode kann unabhängig aktualisiert werden, wenn die Core-Versionsfixierung unverändert bleibt. Aktualisieren Sie die Kunden-Image-Tags in `docker-compose.yml`, laden Sie die neuen Images herunter und starten Sie die Kundendienste neu.

Wenn Kundencode eine neue Core-Version übernimmt, aktualisieren Sie die Core-Versionsfixierung in `pyproject.toml`, erstellen Sie die Kunden-Images neu und deployen Sie dann sowohl Core- als auch Kunden-Updates zusammen.

---

## Rollbacks

### VM-Snapshots

VM-Snapshots erfassen den gesamten Systemzustand. Ein Rollback stellt die komplette VM aus einem Pre-Update-Snapshot wieder her und setzt alle Services gleichzeitig in ihren vorherigen Zustand zurück.

### Versionstags

Bleiben die Daten mit der vorherigen Version kompatibel, kann ein Rollback durch Zurücksetzen der Image-Tags in `docker-compose.yml` auf die vorherigen Versionen, Herunterladen dieser Images und Neustarten der Services durchgeführt werden.

Core- und Kundencode können unabhängig voneinander zurückgerollt werden, wenn sie separat aktualisiert wurden. Wenn beide zusammen aktualisiert wurden, rollen Sie zuerst den Core zurück, dann den Kundencode.

---

## Kompatibilität

Kundencode fixiert sich auf bestimmte Core-Versionen, um die Stabilität zu gewährleisten. Eine Kompatibilitätsmatrix verfolgt, welche Kundenversionen mit welchen Core-Versionen funktionieren:

| Kundenversion | Core-Version | Status | Anmerkungen |
|-----------------|--------------|--------|-------|
| v1.0.0 | v0.1.2 | Legacy | End of Life |
| v1.1.0 | v1.2.3 | Unterstützt | Aktuelle Produktion |
| v1.2.0 | v1.2.3 | Unterstützt | Neueste Funktionen |
| v2.0.0 | v2.3.4 | Testphase | Nächstes Major Release |

Staging-Umgebungen sollten der Produktionsinfrastruktur entsprechen und repräsentative Datensätze für die Kompatibilitätstests vor Produktions-Updates verwenden.

---

## Monitoring

Der Observability Stack umfasst Phoenix für AI-spezifisches Tracing, OpenTelemetry für verteiltes Tracing und optional SigNoz Cloud für externe Metriken und Logs. Überwachen Sie Core-Services (API, Web, Dagster) und Kundenservices (Agents, Pipelines, Prozesse) während und nach Updates.

---

## Zugehörige Dokumentation

- [Bereitstellungsoptionen](../1_deployment_options/) - Mandantenfähige Architektur
- [Backup und Wiederherstellung](../4_backup_and_recovery/) - Backup-Strategien
- [Core-Komponenten](../../2_architecture/1_core_components/) - Komponentenabhängigkeiten
