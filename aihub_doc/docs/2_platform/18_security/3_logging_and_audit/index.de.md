---
title: Protokollierung, Speicherung & Audit-Trails
index: 3
---

# Protokollierung, Speicherung & Audit-Trails

::: info Hinweis zur Dokumentation
Die englische Version dieser Dokumentation ist die maßgebliche und vollständige Version. Diese deutsche Version ist eine Zusammenfassung der wichtigsten Punkte.

Vollständige Dokumentation: [English Version](./index.en.md)
:::

## Überblick

Der Swiss AI Hub implementiert umfassende Protokollierungs- und Audit-Funktionen für Unternehmenssicherheit, Compliance und Betriebsanforderungen.

## Log-Erfassungsarchitektur

### Multi-Layer Log-Erfassung

Die Plattform erfasst Logs aus mehreren Quellen:

- **Anwendungslogs**: Strukturierte Protokollierung von allen Python-Services
- **Container-Logs**: Ausgabe von Docker-Containern
- **HTTP-Request-Logs**: Detaillierte Aufzeichnungen aller API-Interaktionen
- **Sicherheitsereignislogs**: Authentifizierung, Berechtigungsprüfungen, administrative Aktionen
- **AI-Betriebslogs**: LLM-Anfragen, Token-Verbrauch, Agent-Workflow-Ausführungen

### Strukturiertes Logging-Format

Alle Logs werden im strukturierten JSON-Format ausgegeben:

```json
{
  "timestamp": "2025-10-17T15:21:12.028Z",
  "level": "INFO",
  "logger": "aihub_api.auth",
  "message": "User authenticated successfully",
  "user_id": "user@example.com",
  "trace_id": "a1b2c3d4e5f6"
}
```

## Log-Speicherung und Aufbewahrung

### Zentralisierte Log-Aggregation

Alle Logs werden in der **SigNoz** Observability-Plattform zentralisiert:

- Einheitlicher Zugriffspunkt für alle Service-Logs
- Automatische Korrelation mit Traces und Metriken
- Effiziente spaltenbasierte Speicherung mit Kompression
- Schnelle Abfrage über Millionen von Log-Einträgen

### Standard-Aufbewahrungsfristen

- **Betriebslogs** (INFO, DEBUG): 30 Tage im Hot-Storage, 90 Tage im Archiv
- **Sicherheits-Audit-Logs**: 90 Tage im Hot-Storage, 7 Jahre im Archiv
- **Fehlerprotokolle** (ERROR, CRITICAL): 90 Tage im Hot-Storage, 1 Jahr im Archiv
- **AI-Betriebslogs**: 30 Tage im Hot-Storage, 90 Tage im Archiv

### Log-Rotation und Archivierung

**Automatische Rotation**: Logs werden automatisch rotiert basierend auf:
- Zeitbasiert: Tägliche oder wöchentliche Rotation
- Größenbasiert: Rotation bei konfigurierten Größenschwellenwerten

**Archivierungsprozess**:
1. Kompression rotierter Logs
2. Verschlüsselung mit AES-256
3. Metadaten-Erhaltung für Durchsuchbarkeit
4. Integritätsprüfung mit Prüfsummen

## Sicherheitsereignisprotokollierung

Jedes sicherheitsrelevante Ereignis wird mit vollständigem Kontext protokolliert:

- Erfolgreiche Authentifizierung
- Fehlgeschlagene Authentifizierung
- Berechtigungsprüfungen
- Zugriff verweigert
- Administrative Aktionen
- Konfigurationsänderungen
- Datenzugriff auf Wissensdatenbanken

## Aktivitätsprotokollierung und Protokoll

### Benutzeraktivitäts-Tracking

Umfassendes Tracking von Benutzerinteraktionen:

- Konversations-Tracking
- Ressourcennutzung (Token-Verbrauch, Abfragehäufigkeit)
- Workflow-Ausführung
- Genehmigungs-Entscheidungen

### Compliance- und behördliche Berichterstattung

**Audit-Log-Export**: Compliance-Berichte generieren:
- Benutzerzugriffsmuster
- Berechtigungsänderungen
- Datenzugriff
- Systemänderungen

**Berichtsformate**: CSV/Excel, JSON, PDF, SIEM-Integration

## Weitere Informationen

Vollständige Details zu Log-Abfrage, Korrelation, Datenschutz, DSGVO-Compliance und Best Practices finden Sie in der [englischen Vollversion](./index.en.md).
