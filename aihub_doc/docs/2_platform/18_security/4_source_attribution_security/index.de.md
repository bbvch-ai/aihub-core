---
title: Sicherheit bei Quellenangaben
index: 4
---

# Sicherheit bei Quellenangaben

::: info Hinweis zur Dokumentation
Die englische Version dieser Dokumentation ist die maßgebliche und vollständige Version. Diese deutsche Version ist eine Zusammenfassung der wichtigsten Punkte.

Vollständige Dokumentation: [English Version](./index.en.md)
:::

## Überblick

Der Swiss AI Hub implementiert umfassende Sicherheitsmaßnahmen für Quellenangaben und externe Referenzen, um sicherzustellen, dass aus Wissensdatenbanken und externen Quellen abgerufene Informationen sicher, vertrauenswürdig und compliant sind.

## Quellreferenz-Validierung

### URL-Bereinigung und -Validierung

Alle URLs in Quellenangaben durchlaufen strenge Validierung:

**Protokoll-Whitelisting**: Nur sichere Protokolle sind erlaubt:
- `https://` - Sichere Web-Ressourcen (bevorzugt)
- `http://` - Nicht-sichere Web-Ressourcen (mit Warnhinweis)
- `file://` - Interne Dateireferenzen (eingeschränkt auf autorisierte Benutzer)

Blockierte Protokolle:
- `javascript:` - Script-Ausführungsvektoren
- `data:` - Inline-Daten-URIs mit ausführbarem Code
- Alle nicht explizit genehmigten benutzerdefinierten Protokolle

### Content Security Policy (CSP) für Quellenlinks

Externe Links werden mit Sicherheitsattributen geöffnet:

```html
<a href="https://trusted-source.com/doc.pdf" 
   target="_blank" 
   rel="noopener noreferrer nofollow">
    Dokumentenquelle
</a>
```

**Sicherheitsattribute**:
- `target="_blank"`: Öffnet in neuem Tab
- `rel="noopener"`: Verhindert Zugriff auf window.opener
- `rel="noreferrer"`: Entfernt Referrer-Informationen
- `rel="nofollow"`: SEO-Schutz

### Dateipfad-Bereinigung

Interne Dateireferenzen durchlaufen zusätzliche Bereinigung:

- **Path-Traversal-Verhinderung**: Blockierung von `../` Sequenzen
- **Sensible Pfadfilterung**: Blockierung von Systemverzeichnissen
- **Pfadnormalisierung**: Kanonische Form

## Dokument-Metadaten-Sicherheit

### Metadaten-Bereinigung bei der Aufnahme

Wenn Dokumente in Wissensdatenbanken aufgenommen werden, werden Metadaten bereinigt:

- **HTML und Script-Entfernung**: Alle HTML-Tags und Skripte aus Metadatenfeldern entfernen
- **Zeichenkodierung-Validierung**: Sichere Zeichenkodierungen sicherstellen
- **Größenbeschränkungen**: Maximale Größen für Metadatenfelder durchsetzen

### XSS-Verhinderung in Quellenangaben

Quellenangaben in der UI sind gegen XSS-Angriffe geschützt:

- **Ausgabekodierung**: Alle benutzergenerierten Inhalte werden HTML-kodiert
- **Template-Injection-Verhinderung**: Verwendung parametrisierter Templates
- **Framework-Schutz**: Nutzung von Framework-Level XSS-Schutz

## Externe Ressourcensicherheit

### Konfigurierbare externe Zugriffsrichtlinien

Organisationen können Richtlinien für den Zugriff auf externe Ressourcen konfigurieren:

- **Domain-Whitelisting**: Genehmigte externe Domains definieren
- **Zugriffskontrolle nach Benutzerrolle**: Verschiedene Berechtigungen für verschiedene Benutzer
- **Netzwerk-Level-Beschränkungen**: Für air-gapped oder hochsichere Deployments

### Sichere externe Inhaltsabruf

Wenn die Plattform externe Inhalte abrufen muss:

- **Proxy durch Sicherheits-Gateway**: Alle externen Anfragen über Sicherheits-Proxy
- **Timeout- und Größenbeschränkungen**: Ressourcenerschöpfung verhindern
- **SSL/TLS-Verifikation**: Immer SSL-Zertifikate für HTTPS-Anfragen verifizieren

## Weitere Informationen

Vollständige Details zu Knowledge-Base-Zugriffskontrolle, Web-Suche-Integration, Dokument-Upload-Sicherheit, Compliance und Best Practices finden Sie in der [englischen Vollversion](./index.en.md).
