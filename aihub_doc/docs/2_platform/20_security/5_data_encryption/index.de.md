---
title: Datenverschlüsselung
source_sha: fc861922e54a08747748a05d18391f315fdb9bb2e0010dcfdc50ea87ed788b8f
---

# Datenverschlüsselung im Ruhezustand

> **️⚠️Implementierungsstatus**: Dieser Verschlüsselungsansatz ist noch nicht implementiert. Dieser Abschnitt beschreibt
> das geplante Sicherheitskonzept.

## LUKS-Volume-Verschlüsselung

Alle Plattformdaten werden in Docker-Volumes gespeichert, die mit Linux Unified Key Setup (LUKS) verschlüsselt sind.
Dieser Ansatz bietet eine vollständige Festplattenverschlüsselung für alle persistenten Daten, die von der Plattform
gespeichert werden, einschließlich:

- Anwendungsdatenbanken
- Vektorspeicher-Indizes
- Dokumentspeicher- und Ingestionsartefakte
- Konfigurationsdaten und Geheimnisse
- Logs und Observability-Daten

### Sicherheitseigenschaften

Die LUKS-Verschlüsselung bietet:

- **AES-256-Verschlüsselung** im XTS-Modus für das gesamte Volume
- **Schlüsselmanagement** unabhängig von den Daten, das eine Schlüsselrotation ohne Neuverschlüsselung des gesamten
  Volumes ermöglicht
- **Schutz vor physischem Zugriff**: Daten bleiben verschlüsselt, wenn das System ausgeschaltet oder Volumes getrennt
  werden
- **Transparenter Betrieb**: Anwendungen interagieren unverändert mit verschlüsselten Volumes; die Ver-/Entschlüsselung
  erfolgt auf der Blockgeräteebene

### Bedrohungsabwehr

Diese Strategie der Verschlüsselung im Ruhezustand schützt vor:

- Unbefugtem physischem Zugriff auf Speichermedien
- Exfiltration von Volume-Snapshots
- Festplattendiebstahl oder unsachgemäße Entsorgung
- Kompromittierung von Backup-Medien

Die Verschlüsselung schützt **nicht** vor Bedrohungen, während das System läuft und Volumes gemountet sind, wie z. B.
speicherbasierte Angriffe oder kompromittierte Anwendungszugangsdaten. Diese Bedrohungen werden durch ergänzende
Kontrollen im Zugriffsmanagement, der Netzwerksegmentierung und der Laufzeit-Sicherheitsüberwachung angegangen.

# Datenverschlüsselung während der Übertragung

Alle Daten, die zwischen der Plattform und externen Clients sowie Verbindungen zu externen Services übertragen werden,
werden mithilfe branchenüblicher Transport Layer Security (TLS)-Protokolle verschlüsselt.

## Edge-Verschlüsselung

Die Plattform verwendet **Traefik** als Reverse-Proxy und Ingress-Controller, der die TLS-Terminierung am Netzwerkrands
bereitstellt. Alle externen Verbindungen werden durch Folgendes gesichert:

- Unterstützung für **TLS 1.2 und TLS 1.3** für Client-Verbindungen
- **Automatische HTTP- zu HTTPS-Weiterleitung**, die sicherstellt, dass der gesamte Traffic verschlüsselte Kanäle
  verwendet
- **Let's Encrypt-Integration** für die automatisierte Zertifikatsbereitstellung und -erneuerung in
  Produktionsumgebungen
- **Unterstützung für benutzerdefinierte Zertifikate** für Umgebungen mit bestehender PKI-Infrastruktur

### Zertifikatsmanagement in der Produktion

In Produktions-Deployments werden TLS-Zertifikate über Folgendes verwaltet:

- **ACME-Protokoll** mit Let's Encrypt für die automatische Zertifikatsausstellung und -erneuerung
- **Zertifikatsvalidierung** über den HTTP-01-Challenge-Mechanismus
- **Automatisierte Rotation** vor dem Ablaufdatum, um Service-Unterbrechungen zu vermeiden

### Sicherheits-Header

Traefik wendet sicherheitsgehärtete HTTP-Header auf alle Antworten an:

- **Strict-Transport-Security (HSTS)**: Erzwingt HTTPS für ein Jahr, einschließlich aller Subdomains
- **Content-Security-Policy**: Beschränkt das Frame-Embedding auf Same-Origin
- **X-Content-Type-Options**: Verhindert MIME-Typ-Sniffing
- **Referrer-Policy**: Begrenzt das Leck von Referrer-Informationen

## Verbindungen zu externen Services

Alle Verbindungen von der Plattform zu externen Services nutzen verschlüsselten Transport:

- **Swiss LLM Cloud**: HTTPS-Verbindungen zu den konfigurierten Swiss LLM Cloud Endpunkten
- **OAuth/OIDC Providers**: TLS-gesicherte Authentifizierungs-Workflows
- **LLM Providers**: Verschlüsselte API-Verbindungen über die LiteLLM-Proxy-Schicht

### Zertifikatsvalidierung

Die Plattform validiert Serverzertifikate für alle externen Verbindungen und schützt so vor Man-in-the-Middle-Angriffen.
Standardbibliotheks-TLS-Implementierungen stellen sicher:

- **Zertifikatskettenprüfung** gegen vertrauenswürdige Root-CAs
- **Hostnamenvalidierung**, die den Zertifikats-Subject Alternative Names entspricht
- **Widerrufsprüfung**, wo vom Service unterstützt

## Interne Kommunikation

Die Kommunikation zwischen Docker-Containern innerhalb desselben Deployments verwendet das interne Docker-Netzwerk.
Obwohl dieser Traffic durch die Netzwerksegmentierung von Docker von externen Netzwerken isoliert ist, ist er **nicht
auf der Anwendungsschicht verschlüsselt**. Das Sicherheitsmodell basiert auf:

- **Netzwerkisolation**: Container-zu-Container-Traffic durchläuft niemals externe Netzwerke
- **Firewall-Grenzen**: Der Netzwerk-Stack des Docker-Hosts bietet Isolation vor externem Zugriff
- **Physische/virtuelle Sicherheit**: Die VM- oder Host-Umgebung bildet den Sicherheitsperimeter

Für Deployments, die eine verschlüsselte Inter-Service-Kommunikation erfordern (z. B. Multi-Host-Deployments), können
zusätzliche Maßnahmen wie Service Mesh oder IPsec implementiert werden.

## WebSocket-Verbindungen

Echtzeit-Event-Streaming über WebSocket-Verbindungen wird gesichert durch:

- **WSS (WebSocket Secure)**: TLS-verschlüsseltes WebSocket-Protokoll für Client-Verbindungen
- **Origin-Validierung**: Überprüft den Origin-Header, um Cross-Site-WebSocket-Hijacking zu verhindern
- **Session-basierte Authentifizierung**: Erfordert eine gültige Authentifizierung, bevor auf WebSocket upgegradet wird
