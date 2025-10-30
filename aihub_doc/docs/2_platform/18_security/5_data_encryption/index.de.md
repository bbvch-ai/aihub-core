---
title: Datenverschlüsselung
source_sha: 83b056ccf57a3538d4fbd4682d7a77804050a25f046e813adf0c6e9c550f79c6
---

# Datenverschlüsselung im Ruhezustand

> **️⚠️Implementierungsstatus**: Dieser Verschlüsselungsansatz ist noch nicht implementiert. Dieser Abschnitt beschreibt
> das geplante Sicherheitskonzept.

## LUKS-Datenträgerverschlüsselung

Alle Plattformdaten werden in Docker-Volumes gespeichert, die mit Linux Unified Key Setup (LUKS) verschlüsselt sind.
Dieser Ansatz bietet eine vollständige Datenträgerverschlüsselung für alle persistenten Daten, die von der Plattform
gespeichert werden, einschließlich:

- Anwendungsdatenbanken
- Vektorspeicherindizes
- Dokumentenspeicherung und Ingestionsartefakte
- Konfigurationsdaten und Geheimnisse
- Protokolle und Observabilitätsdaten

### Sicherheitseigenschaften

Die LUKS-Verschlüsselung bietet:

- **AES-256-Verschlüsselung** im XTS-Modus für das gesamte Volume
- **Schlüsselverwaltung** unabhängig von den Daten, die eine Schlüsselrotation ohne Neuverschlüsselung des gesamten
  Volumes ermöglicht
- **Schutz vor physischem Zugriff**: Daten bleiben verschlüsselt, wenn das System ausgeschaltet ist oder Volumes
  getrennt werden
- **Transparenter Betrieb**: Anwendungen interagieren ohne Modifikation mit verschlüsselten Volumes;
  Ver-/Entschlüsselung erfolgt auf der Blockgeräteschicht

### Bedrohungsabwehr

Diese Verschlüsselungsstrategie im Ruhezustand schützt vor:

- Unbefugtem physischen Zugriff auf Speichermedien
- Exfiltration von Volume-Snapshots
- Festplattendiebstahl oder unsachgemäßer Entsorgung
- Kompromittierung von Sicherungsmedien

Die Verschlüsselung schützt **nicht** vor Bedrohungen, während das System läuft und Volumes gemountet sind, wie z.B.
speicherbasierte Angriffe oder kompromittierte Anmeldeinformationen von Anwendungen. Diese Bedrohungen werden durch
ergänzende Kontrollen in der Zugriffsverwaltung, Netzwerksegmentierung und Laufzeit-Sicherheitsüberwachung adressiert.

# Datenverschlüsselung während der Übertragung

Alle Daten, die zwischen der Plattform und externen Clients sowie Verbindungen zu externen Diensten übertragen werden,
werden mithilfe von Industriestandard-TLS-Protokollen (Transport Layer Security) verschlüsselt.

## Edge-Verschlüsselung

Die Plattform setzt **Traefik** als Reverse Proxy und Ingress Controller ein, der die TLS-Terminierung am Netzwerkrand
bereitstellt. Alle externen Verbindungen werden gesichert durch:

- **TLS 1.2 und TLS 1.3** Unterstützung für Client-Verbindungen
- **Automatische HTTP- zu HTTPS-Weiterleitung**, die sicherstellt, dass der gesamte Datenverkehr verschlüsselte Kanäle
  nutzt
- **Let's Encrypt-Integration** für die automatisierte Bereitstellung und Erneuerung von Zertifikaten in
  Produktionsumgebungen
- **Unterstützung für benutzerdefinierte Zertifikate** für Umgebungen mit bestehender PKI-Infrastruktur

### Zertifikatsverwaltung in Produktionsumgebungen

In Produktionsbereitstellungen werden TLS-Zertifikate verwaltet durch:

- **ACME-Protokoll** mit Let's Encrypt zur automatischen Zertifikatsausstellung und -erneuerung
- **Zertifikatsvalidierung** über den HTTP-01-Challenge-Mechanismus
- **Automatisierte Rotation** vor Ablauf, wodurch Dienstunterbrechungen verhindert werden

### Sicherheits-Header

Traefik wendet sicherheitsgehärtete HTTP-Header auf alle Antworten an:

- **Strict-Transport-Security (HSTS)**: Erzwingt HTTPS für ein Jahr, einschließlich aller Subdomains
- **Content-Security-Policy**: Beschränkt das Einbetten von Frames auf Same-Origin
- **X-Content-Type-Options**: Verhindert MIME-Typ-Sniffing
- **Referrer-Policy**: Begrenzt die Offenlegung von Referrer-Informationen

## Verbindungen zu externen Diensten

Alle Verbindungen von der Plattform zu externen Diensten nutzen verschlüsselten Transport:

- **Azure OpenAI Services**: HTTPS-Verbindungen zu `*.openai.azure.com` und `*.cognitiveservices.azure.com`
- **OAuth/OIDC-Anbieter**: TLS-gesicherte Authentifizierungsabläufe
- **LLM-Anbieter**: Verschlüsselte API-Verbindungen über die LiteLLM-Proxy-Schicht
- **Azure AI Services**: HTTPS für Document Intelligence, Speech Services und Cognitive Search

### Zertifikatsvalidierung

Die Plattform validiert Serverzertifikate für alle externen Verbindungen und schützt so vor Man-in-the-Middle-Angriffen.
Standard-TLS-Bibliotheksimplementierungen gewährleisten:

- **Verifizierung der Zertifikatskette** gegen vertrauenswürdige Root-CAs
- **Hostname-Validierung**, die den Subject Alternative Names des Zertifikats entspricht
- **Widerrufsprüfung**, sofern vom Dienst unterstützt

## Interne Kommunikation

Die Kommunikation zwischen Docker-Containern innerhalb derselben Bereitstellung nutzt das interne Docker-Netzwerk.
Obwohl dieser Datenverkehr durch die Netzwerksegmentierung von Docker von externen Netzwerken isoliert ist, ist er **auf
der Anwendungsebene nicht verschlüsselt**. Das Sicherheitsmodell basiert auf:

- **Netzwerkisolation**: Der Container-zu-Container-Verkehr durchläuft niemals externe Netzwerke
- **Firewall-Grenzen**: Der Netzwerk-Stack des Docker-Hosts bietet Isolation vor externem Zugriff
- **Physische/virtuelle Sicherheit**: Die VM- oder Hostumgebung bietet den Sicherheitsperimeter

Für Bereitstellungen, die eine verschlüsselte Inter-Service-Kommunikation erfordern (z.B. Multi-Host-Bereitstellungen),
können zusätzliche Maßnahmen wie Service Mesh oder IPsec implementiert werden.

## WebSocket-Verbindungen

Echtzeit-Ereignis-Streaming über WebSocket-Verbindungen wird gesichert durch:

- **WSS (WebSocket Secure)**: TLS-verschlüsseltes WebSocket-Protokoll für Client-Verbindungen
- **Origin-Validierung**: Überprüft den Origin-Header, um Cross-Site-WebSocket-Hijacking zu verhindern
- **Sitzungsbasierte Authentifizierung**: Erfordert eine gültige Authentifizierung, bevor auf WebSocket aktualisiert
  wird
