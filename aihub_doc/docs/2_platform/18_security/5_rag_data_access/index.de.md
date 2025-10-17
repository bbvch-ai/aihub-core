---
title: RAG-Datenzugriffsverwaltung
index: 5
---

# RAG-Datenzugriffsverwaltung

::: info Hinweis zur Dokumentation
Die englische Version dieser Dokumentation ist die maßgebliche und vollständige Version. Diese deutsche Version ist eine Zusammenfassung der wichtigsten Punkte.

Vollständige Dokumentation: [English Version](./index.en.md)
:::

## Überblick

Der Swiss AI Hub implementiert umfassende Datenzugriffskontrollen für Retrieval-Augmented Generation (RAG) Systeme, um sicherzustellen, dass sensible Informationen in Wissensdatenbanken nur von autorisierten Benutzern zugegriffen werden können.

## Knowledge-Base-Zugriffskontrollarchitektur

### Hierarchische Wissensorganisation

Wissensdatenbanken sind in einer hierarchischen Struktur organisiert:

```
Firmenwissen
├── Öffentlich
│   ├── Pressemitteilungen
│   └── Produktdokumentation
├── Intern
│   ├── Engineering
│   ├── HR
│   └── Finanzen
└── Vertraulich
    ├── Rechtliches
    └── Executive
```

### Berechtigungsmodell für Wissensdatenbanken

Zugriff auf Wissensdatenbanken folgt dem hierarchischen RBAC-System der Plattform:

- `aihub.user.knowledge.public` - Zugriff auf alle öffentlichen Wissensdatenbanken
- `aihub.user.knowledge.internal.hr` - Zugriff auf HR-Dokumente
- `aihub.user.knowledge.internal.hr.policies` - Zugriff nur auf HR-Richtlinien
- `aihub.admin.knowledge.internal.hr` - Administrativer Zugriff auf HR-Wissensdatenbank

## Abfragezeit-Zugriffs-Filterung

### Retrieval-Pipeline mit Zugriffskontrolle

Bei einer Benutzerabfrage an einen RAG-Agenten erzwingt die Retrieval-Pipeline Zugriffskontrollen:

1. Zugängliche Wissensdatenbanken identifizieren
2. Vom Vektorspeicher mit Namespace-Filter abrufen
3. Dokument-Level-Filter anwenden
4. Zugriff für Audit protokollieren

### Namespace-basierte Filterung

- Dokumente werden in namespace-partitionierten Sammlungen gespeichert
- Abfragen durchsuchen nur Namespaces mit Zugriffsberechtigung
- Reduzierter Suchraum verbessert Performance

### Dokument-Level-Zugriffskontrolle

Jedes Dokument enthält Zugriffskontroll-Metadaten:

```json
{
  "document_id": "doc_12345",
  "metadata": {
    "namespace": "internal.hr.policies",
    "classification": "internal",
    "owner": "hr_team",
    "tags": ["policy", "vacation"],
    "access_groups": ["hr", "management"]
  }
}
```

## Erweiterte Zugriffskontrollmuster

### Attributbasierte Zugriffskontrolle (ABAC)

Über einfache Namespace-Berechtigungen hinaus unterstützt die Plattform attributbasierte Zugriffskontrolle:

**Benutzerattribute**:
- Abteilung
- Jobstufe
- Standort
- Freigabestufe

**Dokumentattribute**:
- Klassifizierung
- Abteilung
- Aufbewahrungsfrist
- Sensitivitäts-Tags

### Zeitbasierte Zugriffskontrolle

**Temporäre Zugriffszuweisungen**: Zeitlich begrenzten Zugriff gewähren:

- Externe Prüfer mit temporärem Zugriff auf Finanzdokumente
- Auftragnehmer für spezifische Projekte
- Notfallzugriff bei Vorfallreaktion

### Kontextabhängige Zugriffskontrolle

Zugriff basierend auf Kontext:

- Standortbasierte Beschränkungen
- Zeitbasierte Beschränkungen (z.B. nur während Geschäftszeiten)
- Zweckbasierter Zugriff (Begründung erforderlich)

## Datenisolationsmuster

### Multi-Tenant-Wissensdatenbanken

Für Deployments, die mehrere Organisationen bedienen:

- **Tenant-Isolation**: Jeder Tenant hat vollständig isolierte Wissensdatenbanken
- **Tenant-Partitionierung**: Separate Vektorspeicher-Sammlungen pro Tenant
- **Isolierte Suchindizes**

## Performance-Optimierung

### Caching-Strategien

- **Berechtigungs-Cache**: Berechtigungsbewertungsergebnisse cachen
- **Namespace-Vorberechnung**: Zugängliche Namespaces für Rollen vorberechnen

### Effiziente Filterungsstrategien

- **Vorfilterung im Vektorspeicher**: Filterung auf Vektorspeicher-Ebene durchführen
- **Batch-Berechtigungsprüfungen**: Berechtigungen für mehrere Dokumente parallel prüfen

## Audit und Compliance

### Retrieval-Zugriffsprotokollierung

Jede Dokumentenabrufung wird für Audit-Zwecke protokolliert:

- Welche Benutzer auf welche Dokumente zugegriffen haben
- Zugriffshäufigkeit auf sensible Dokumente
- Nicht autorisierte Zugriffsversuche
- Datenzugriffsmuster nach Abteilung

## Weitere Informationen

Vollständige Details zu erweiterten Zugriffsmustern, Performance-Optimierung, Compliance-Berichterstattung und Best Practices finden Sie in der [englischen Vollversion](./index.en.md).
