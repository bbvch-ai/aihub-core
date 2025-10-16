---
title: Datenverschlüsselung
index: 1
source_sha: "33b1a1ef4327a33eeb7a50c66ce7fc17df1585b201c72d442cb1defde22f115a"
---

# Datenverschlüsselung im Ruhezustand

> **️⚠️Implementierungsstatus**: Dieser Verschlüsselungsansatz ist noch nicht implementiert. Dieser Abschnitt beschreibt das geplante Sicherheitskonzept.

## LUKS-Volumenverschlüsselung

Alle Plattformdaten werden in Docker-Volumes gespeichert, die mittels Linux Unified Key Setup (LUKS) verschlüsselt sind. Dieser Ansatz bietet eine vollständige Festplattenverschlüsselung für alle persistenten Daten, die von der Plattform gespeichert werden, einschließlich:

- Anwendungsdatenbanken
- Vektor-Speicher-Indizes
- Dokumentenspeicher und Ingestions-Artefakte
- Konfigurationsdaten und Geheimnisse
- Protokolle und Observability-Daten

### Sicherheitseigenschaften

Die LUKS-Verschlüsselung bietet:

- **AES-256-Verschlüsselung** im XTS-Modus für das gesamte Volumen
- **Schlüsselverwaltung** unabhängig von den Daten, was eine Schlüsselrotation ohne Neuverschlüsselung des gesamten Volumens ermöglicht
- **Schutz vor physischem Zugriff**: Daten bleiben verschlüsselt, wenn das System ausgeschaltet ist oder Volumes getrennt werden
- **Transparenter Betrieb**: Anwendungen interagieren unverändert mit verschlüsselten Volumes; Ver- und Entschlüsselung erfolgen auf der Blockgeräteebene

### Bedrohungsminderung

Diese Strategie zur Verschlüsselung im Ruhezustand schützt vor:

- Unbefugtem physischen Zugriff auf Speichermedien
- Exfiltration von Volume-Snapshots
- Diebstahl oder unsachgemäßer Entsorgung von Festplatten
- Kompromittierung von Backup-Medien

Die Verschlüsselung schützt **nicht** vor Bedrohungen, während das System läuft und Volumes gemountet sind, wie z.B. speicherbasierte Angriffe oder kompromittierte Anmeldeinformationen von Anwendungen. Diese Bedrohungen werden durch ergänzende Kontrollen im Zugriffsmanagement, der Netzwerksegmentierung und der Laufzeitsicherheitsüberwachung adressiert.

# Datenverschlüsselung während der Übertragung

Alle Daten, die zwischen der Plattform und externen Clients sowie Verbindungen zu externen Diensten übertragen werden, sind mittels branchenüblicher Transport Layer Security (TLS)-Protokolle verschlüsselt.

## Edge-Verschlüsselung

Die Plattform nutzt **Traefik** als Reverse Proxy und Ingress Controller, der die TLS-Terminierung am Netzwerkrand bereitstellt. Alle externen Verbindungen werden durch folgendes gesichert:

- Unterstützung für **TLS 1.2 und TLS 1.3** für Client-Verbindungen
- **Automatische HTTP-zu-HTTPS-Umleitung**, die sicherstellt, dass der gesamte Datenverkehr verschlüsselte Kanäle verwendet
- **Let's Encrypt-Integration** für die automatisierte Zertifikatsbereitstellung und -erneuerung in Produktionsumgebungen
- **Unterstützung für benutzerdefinierte Zertifikate** für Umgebungen mit bestehender PKI-Infrastruktur

### Verwaltung von Produktionszertifikaten

In Produktionsumgebungen werden TLS-Zertifikate über Folgendes verwaltet:

- **ACME-Protokoll** mit Let's Encrypt für die automatische Ausstellung und Erneuerung von Zertifikaten
- **Zertifikatsvalidierung** über den HTTP-01-Challenge-Mechanismus
- **Automatisierte Rotation** vor dem Ablauf, um Dienstunterbrechungen zu vermeiden

### Sicherheits-Header

Traefik wendet sicherheitsgehärtete HTTP-Header auf alle Antworten an:

- **Strict-Transport-Security (HSTS)**: Erzwingt HTTPS für ein Jahr, einschließlich aller Subdomains
- **Content-Security-Policy**: Beschränkt das Einbetten von Frames auf Same-Origin
- **X-Content-Type-Options**: Verhindert MIME-Typ-Sniffing
- **Referrer-Policy**: Begrenzt das Durchsickern von Referrer-Informationen

## Externe Dienstverbindungen

Alle Verbindungen von der Plattform zu externen Diensten nutzen verschlüsselte Übertragung:

- **Azure OpenAI Services**: HTTPS-Verbindungen zu `*.openai.azure.com` und `*.cognitiveservices.azure.com`
- **OAuth/OIDC-Anbieter**: TLS-gesicherte Authentifizierungs-Flows
- **LLM-Anbieter**: Verschlüsselte API-Verbindungen über die LiteLLM-Proxy-Schicht
- **Azure AI Services**: HTTPS für Document Intelligence, Speech Services und Cognitive Search

### Zertifikatsvalidierung

Die Plattform validiert Serverzertifikate für alle externen Verbindungen und schützt so vor Man-in-the-Middle-Angriffen. Standard-Bibliotheks-TLS-Implementierungen gewährleisten:

- **Zertifikatskettenprüfung** gegen vertrauenswürdige Stamm-CAs
- **Hostnamenvalidierung**, die den Subject Alternative Names des Zertifikats entspricht
- **Widerrufsprüfung**, sofern vom Dienst unterstützt

## Interne Kommunikation

Die Kommunikation zwischen Docker-Containern innerhalb derselben Bereitstellung nutzt das interne Docker-Netzwerk. Obwohl dieser Datenverkehr durch die Netzwerksegmentierung von Docker von externen Netzwerken isoliert ist, ist er **nicht auf Anwendungsebene verschlüsselt**. Das Sicherheitsmodell beruht auf:

- **Netzwerkisolation**: Der Container-zu-Container-Verkehr durchläuft niemals externe Netzwerke
- **Firewall-Grenzen**: Der Netzwerk-Stack des Docker-Hosts bietet Isolation von externem Zugriff
- **Physische/virtuelle Sicherheit**: Die VM- oder Host-Umgebung bildet den Sicherheitsperimeter

Für Bereitstellungen, die eine verschlüsselte Inter-Service-Kommunikation erfordern (z.B. Multi-Host-Bereitstellungen), können zusätzliche Maßnahmen wie Service Mesh oder IPsec implementiert werden.

## WebSocket-Verbindungen

Echtzeit-Event-Streaming über WebSocket-Verbindungen wird durch Folgendes gesichert:

- **WSS (WebSocket Secure)**: TLS-verschlüsseltes WebSocket-Protokoll für Client-Verbindungen
- **Origin-Validierung**: Überprüft den Origin-Header, um Cross-Site-WebSocket-Hijacking zu verhindern
- **Sitzungsbasierte Authentifizierung**: Erfordert eine gültige Authentifizierung, bevor auf WebSocket aktualisiert wird
