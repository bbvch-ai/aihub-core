---
title: Updates & Wartung
source_sha: b180206389a34739ba5d50aa69e316da0b661b5ee7a48ebb4bea477fc63c74c5
---

# Updates und Wartung

## Architektur

Der AI-Hub trennt Kernplattformkomponenten von kundenspezifischem Code. Die Kernplattform (dieses Repository) enthält
gemeinsame grundlegende Komponenten wie API, Web, Dagster und Bot. Kunden-Repositories enthalten benutzerdefinierte
Agents, Pipelines und Prozesse. Beide verwenden unabhängige semantische Versionierung und können separat aktualisiert
werden.

Kundencode fixiert sich über `pyproject.toml` auf eine bestimmte Core-Version:

```toml
[project.dependencies]
aihub-core = { git = "https://github.com/bbvch-ai/aihub-core.git", tag = "v1.2.3" }
```

Das bedeutet, dass Core-Updates Kunden-Deployments nicht automatisch beeinflussen. Kunden kontrollieren, wann sie neue
Core-Versionen übernehmen.

______________________________________________________________________

## Versionierung

Die Kernplattform verwendet semantische Versionierung:

- Major (X.0.0): Breaking Changes und Architekturanpassungen
- Minor (0.X.0): Neue Funktionen, abwärtskompatible Änderungen
- Patch (0.0.X): Bugfixes und Sicherheitspatches

Drei Versionstags sind verfügbar:

| Tag       | Beschreibung               | Stabilität |
| --------- | -------------------------- | ---------- |
| `latest`  | Neueste stabile Version    | Hoch       |
| `nightly` | Neuester Entwicklungsbuild | Mittel     |
| `v1.2.3`  | Spezifisches Versionstag   | Höchst     |

Kundencode verwendet eigene unabhängige Versionsnummern.

### Release-Prozess

Wenn ein PR mit einem Versionslabel (`major`, `minor` oder `patch`) in `main` gemerged wird, berechnet CI/CD die neue
Version und erstellt ein Git-Tag. Dies löst Komponenten-Builds für betroffene Services aus. Docker-Images werden mit dem
Versionstag nach `ghcr.io/bbvch-ai/aihub-core/*` veröffentlicht. Ein Changelog wird automatisch generiert.

Beispiel-Core-Images:

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

______________________________________________________________________

## Updates

### Core-Plattform-Updates

Abwärtskompatible Core-Updates (Patch- und Minor-Versionen) können durch Aktualisieren der Image-Tags in
`docker-compose.yml`, das Pullen neuer Images und das Neustarten von Services deployed werden. Kundencode läuft
unverändert weiter.

Major-Core-Updates mit Breaking Changes erfordern koordinierte Updates. Kundencode muss aktualisiert werden, um mit der
neuen Core-Version zu funktionieren. Sowohl Core- als auch Kundencode werden gemeinsam während eines Wartungsfensters
aktualisiert.

### Kundencode-Updates

Kundencode kann unabhängig aktualisiert werden, solange der Core-Versions-Pin unverändert bleibt. Aktualisieren Sie die
Kunden-Image-Tags in `docker-compose.yml`, pullen Sie die neuen Images und starten Sie die Kunden-Services neu.

Wenn Kundencode eine neue Core-Version übernimmt, aktualisieren Sie den Core-Versions-Pin in `pyproject.toml`, bauen Sie
die Kunden-Images neu, und deployen Sie dann Core- und Kunden-Updates gemeinsam.

______________________________________________________________________

## Rollbacks

### VM-Snapshots

VM-Snapshots erfassen den gesamten Systemzustand. Ein Rollback stellt die komplette VM von einem Pre-Update-Snapshot
wieder her, wodurch alle Services sofort in ihren vorherigen Zustand zurückversetzt werden.

### Versionstags

Wenn Daten mit der vorherigen Version kompatibel bleiben, führen Sie ein Rollback durch, indem Sie die Image-Tags in
`docker-compose.yml` auf die vorherigen Versionen zurücksetzen, diese Images pullen und die Services neu starten.

Core- und Kundencode können unabhängig zurückgerollt werden, wenn sie separat aktualisiert wurden. Wenn beide zusammen
aktualisiert wurden, rollen Sie zuerst den Core zurück, dann den Kundencode.

______________________________________________________________________

## Kompatibilität

Kundencode fixiert sich auf spezifische Core-Versionen, um die Stabilität zu gewährleisten. Eine Kompatibilitätsmatrix
verfolgt, welche Kundenversionen mit welchen Core-Versionen funktionieren:

| Kundenversion | Core-Version | Status      | Anmerkungen            |
| ------------- | ------------ | ----------- | ---------------------- |
| v1.0.0        | v0.1.2       | Legacy      | Ende des Supports      |
| v1.1.0        | v1.2.3       | Unterstützt | Aktuelle Produktion    |
| v1.2.0        | v1.2.3       | Unterstützt | Neueste Funktionen     |
| v2.0.0        | v2.3.4       | Testen      | Nächstes Major-Release |

Staging-Umgebungen sollten der Produktionsinfrastruktur entsprechen und repräsentative Datensätze verwenden, um die
Kompatibilität vor Produktions-Updates zu testen.

______________________________________________________________________

## Monitoring

Der Observability Stack umfasst Langfuse für KI-spezifisches Tracing, OpenTelemetry für verteiltes Tracing und optional
SigNoz Cloud für externe Metriken und Logs. Überwachen Sie Core-Services (API, Web, Dagster) und Kunden-Services
(Agents, Pipelines, Prozesse) während und nach Updates.

______________________________________________________________________

## Zugehörige Dokumentation

- [Deployment-Optionen](../1_deployment_options/) – Pro-Instanz-Architektur
- [Multi-Tenancy](../../16_multi_tenancy/) – Logische Trennung innerhalb von Instanzen
- [Backup und Recovery](../4_backup_and_recovery/) – Backup-Strategien
- [Core-Komponenten](../../2_architecture/1_core_components/) – Komponentenabhängigkeiten
