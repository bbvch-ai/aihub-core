---
title: Rollenbasierte Zugriffskontrolle (RBAC)
index: 2
---

# Rollenbasierte Zugriffskontrolle (RBAC)

::: info Hinweis zur Dokumentation
Die englische Version dieser Dokumentation ist die maßgebliche und vollständige Version. Diese deutsche Version ist eine Zusammenfassung der wichtigsten Punkte.

Vollständige Dokumentation: [English Version](./index.en.md)
:::

## Überblick

Der Swiss AI Hub implementiert ein ausgereiftes, hierarchisches RBAC-System (Role-Based Access Control), das Unternehmenssicherheit und detaillierte Kontrolle über alle Aspekte der AI-Plattform bietet.

## Kernkomponenten

### Rollen

Rollen sind benannte Sammlungen von Zugriffsregeln, die definieren, was Benutzer auf der Plattform tun können:

- **Data Scientist**: Zugriff auf Agenten, Evaluierungstools und Wissenserkundung
- **Business Analyst**: Zugriff auf Konversationsverläufe und Berichtsfunktionen
- **Administrator**: Vollzugriff auf Benutzerverwaltung und Systemkonfiguration
- **Content Manager**: Zugriff auf Wissensdatenbank-Verwaltung und Datenaufnahme-Pipelines

### Zugriffsregeln

Zugriffsregeln verwenden eine hierarchische Punkt-Notation-Syntax:

```
aihub.[user|admin].[resource_type].[resource_category].[resource_identifier]
```

**Beispiele:**
- `aihub.user.agent.customer_service.chatbot_v2` - Benutzerzugriff auf eine bestimmte Agent-Instanz
- `aihub.admin.service.roles` - Administrativer Zugriff auf Rollenverwaltung
- `aihub.user.knowledge.hr_documents.policies` - Benutzerzugriff auf einen bestimmten Wissens-Namespace

### Wildcard-Unterstützung

Das System unterstützt verschiedene Wildcard-Muster:

- **`*`**: Passt auf ein einzelnes Pfad-Segment
- **`>`**: Passt auf beliebige verbleibende Pfad-Segmente
- **`?*`**: Passt auf null oder ein Pfad-Segment
- **`?>`**: Passt auf null oder mehr verbleibende Segmente

## Berechtigungsbewertungsprozess

1. **Authentifizierung**: Identität über Enterprise Identity Provider verifizieren
2. **Rollenauflösung**: Alle dem Benutzer zugewiesenen Rollen abrufen
3. **Zugriffsregelsammlung**: Alle Zugriffsregeln sammeln
4. **Berechtigungsprüfung**: Übereinstimmung mit erforderlicher Berechtigung bewerten
5. **Autorisierungsentscheidung**: Zugriff gewähren oder verweigern
6. **Audit-Protokollierung**: Berechtigungsprüfung für Compliance aufzeichnen

## Dynamische Service-Sichtbarkeit

Die Benutzeroberfläche passt sich dynamisch an Berechtigungen an:

- **Berechtigungsgefilterte Navigation**: Nur zugängliche Services werden angezeigt
- **Kontextabhängige Steuerungen**: Unterschiedliche Steuerungen basierend auf Berechtigungsstufe
- **Automatische Updates**: Änderungen sofort in der Benutzeroberfläche reflektiert

## Weitere Informationen

Vollständige Details zu RBAC-Implementierung, Service-spezifischen Berechtigungsmustern, Best Practices und Entwickler-Richtlinien finden Sie in der [englischen Vollversion](./index.en.md).
