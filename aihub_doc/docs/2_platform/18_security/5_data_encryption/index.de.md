---
title: Datenverschlüsselung
source_sha: ca324a1d9d9c9005c8a4cd4d6bbfe37a2135ed977e06a5dc540c542ea16539d9
---

# Datenverschlüsselung im Ruhezustand

> **️⚠️Implementierungsstatus**: Dieser Verschlüsselungsansatz ist noch nicht implementiert. Dieser Abschnitt beschreibt
> das geplante Sicherheitskonzept.

## LUKS-Volume-Verschlüsselung

Alle Plattformdaten werden in Docker-Volumes gespeichert, die mittels Linux Unified Key Setup (LUKS) verschlüsselt sind.
Dieser Ansatz bietet eine vollständige Festplattenverschlüsselung für alle persistenten Daten, die von der Plattform
gespeichert werden, einschließlich:

- Anwendungsdatenbanken
- Vektordatenbank-Indizes
- Dokumentenspeicherung und Ingestions-Artefakte
- Konfigurationsdaten und Geheimnisse
- Protokolle und Observability-Daten

### Sicherheitseigenschaften

LUKS-Verschlüsselung bietet:

- **AES-256-Verschlüsselung** im XTS-Modus für das gesamte Volume
- **Schlüsselverwaltung** unabhängig von den Daten, was eine Schlüsselrotation ohne Neuverschlüsselung des gesamten
  Volumes ermöglicht
- **Schutz vor physischem Zugriff**: Daten bleiben verschlüsselt, wenn das System ausgeschaltet ist oder Volumes
  getrennt werden
- **Transparenter Betrieb**: Anwendungen interagieren ohne Änderungen mit verschlüsselten Volumes;
  Verschlüsselung/Entschlüsselung erfolgt auf der Blockgeräteschicht

### Bedrohungsabwehr

Diese Strategie zur Verschlüsselung im Ruhezustand schützt vor:

- Unbefugtem physischem Zugriff auf Speichermedien
- Exfiltration von Volume-Snapshots
- Diebstahl oder unsachgemäßer Entsorgung von Festplatten
- Kompromittierung von Backup-Medien

Die Verschlüsselung schützt **nicht** vor Bedrohungen, während das System läuft und Volumes gemountet sind, wie z.B.
speicherbasierte Angriffe oder kompromittierte Anmeldeinformationen von Anwendungen. Diese Bedrohungen werden durch
ergänzende Kontrollen in der Zugriffsverwaltung, Netzwerksegmentierung und Laufzeit-Sicherheitsüberwachung adressiert.

# Datenverschlüsselung während der Übertragung

Alle Daten, die zwischen der Plattform und externen Clients sowie Verbindungen zu externen Diensten übertragen werden,
werden mithilfe von Industriestandard-Transport Layer Security (TLS)-Protokollen verschlüsselt.

## Edge-Verschlüsselung

Die Plattform setzt **Traefik** als Reverse-Proxy und Ingress-Controller ein, der die TLS-Terminierung am Netzwerkrand
bereitstellt. Alle externen Verbindungen werden durch folgende Maßnahmen gesichert:

- **TLS 1.2 und TLS 1.3** Unterstützung für Client-Verbindungen
- **Automatische HTTP-zu-HTTPS-Weiterleitung**, die sicherstellt, dass der gesamte Datenverkehr verschlüsselte Kanäle
  nutzt
- **Let's Encrypt-Integration** für die automatisierte Zertifikatsbereitstellung und -erneuerung in
  Produktionsumgebungen
- **Unterstützung benutzerdefinierter Zertifikate** für Umgebungen mit bestehender PKI-Infrastruktur

### Produktionszertifikatsverwaltung

In Produktionsumgebungen werden TLS-Zertifikate verwaltet durch:

- **ACME-Protokoll** mit Let's Encrypt für die automatische Ausstellung und Erneuerung von Zertifikaten
- **Zertifikatsvalidierung** über den HTTP-01-Challenge-Mechanismus
- **Automatisierte Rotation** vor Ablauf, um Dienstunterbrechungen zu vermeiden

### Sicherheits-Header

Traefik wendet sicherheitsgehärtete HTTP-Header auf alle Antworten an:

- **Strict-Transport-Security (HSTS)**: Erzwingt HTTPS für ein Jahr, einschließlich aller Subdomains
- **Content-Security-Policy**: Beschränkt das Einbetten von Frames auf Same-Origin
- **X-Content-Type-Options**: Verhindert MIME-Typ-Sniffing
- **Referrer-Policy**: Begrenzt die Offenlegung von Referrer-Informationen

## Externe Diensteverbindungen

Alle Verbindungen von der Plattform zu externen Diensten nutzen verschlüsselten Transport:

- **Azure OpenAI Services**: HTTPS-Verbindungen zu `*.openai.azure.com` und `*.cognitiveservices.azure.com`
- **OAuth/OIDC-Anbieter**: TLS-gesicherte Authentifizierungsflüsse
- **LLM-Anbieter**: Verschlüsselte API-Verbindungen über die LiteLLM-Proxy-Schicht
- **Azure AI Services**: HTTPS für Document Intelligence, Speech Services und Cognitive Search

### Zertifikatsvalidierung

Die Plattform validiert Serverzertifikate für alle externen Verbindungen und schützt so vor Man-in-the-Middle-Angriffen.
Standard-Bibliothek-TLS-Implementierungen stellen sicher:

- **Überprüfung der Zertifikatskette** gegen vertrauenswürdige Root-CAs
- **Hostname-Validierung**, die den Subject Alternative Names des Zertifikats entspricht
- **Widerrufsprüfung**, wo vom Dienst unterstützt

## Interne Kommunikation

Die Kommunikation zwischen Docker-Containern innerhalb desselben Deployments nutzt das interne Docker-Netzwerk. Obwohl
dieser Datenverkehr durch die Netzwerksegmentierung von Docker von externen Netzwerken isoliert ist, ist er auf der
Anwendungsebene **nicht** verschlüsselt. Das Sicherheitsmodell basiert auf:

- **Netzwerkisolation**: Der Datenverkehr von Container zu Container durchläuft niemals externe Netzwerke
- **Firewall-Grenzen**: Der Netzwerk-Stack des Docker-Hosts bietet Isolation vor externem Zugriff
- **Physische/virtuelle Sicherheit**: Die VM- oder Host-Umgebung stellt den Sicherheitsperimeter bereit

Für Deployments, die eine verschlüsselte Inter-Service-Kommunikation erfordern (z.B. Multi-Host-Deployments), können
zusätzliche Maßnahmen wie Service Mesh oder IPsec implementiert werden.

## WebSocket-Verbindungen

Echtzeit-Event-Streaming über WebSocket-Verbindungen wird gesichert durch:

- **WSS (WebSocket Secure)**: TLS-verschlüsseltes WebSocket-Protokoll für Client-Verbindungen
- **Origin-Validierung**: Überprüft den Origin-Header, um Cross-Site-WebSocket-Hijacking zu verhindern
- **Sitzungsbasierte Authentifizierung**: Erfordert eine gültige Authentifizierung, bevor auf WebSocket hochgestuft wird
