---
title: Datenverschlüsselung
source_sha: 2947bd8ab525f84d11f173ea3986220f4bc95067dc27d1e226a96523cc5ccd14
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

## Geheime Konfigurationsfelder

Unabhängig von der Volume-Verschlüsselung verschlüsselt die Plattform die geheimen Felder von Agent-Profilen und
Wissensquellen-Konfigurationen selbst. Ein Feld ist geheim, wenn sein Formular es als Passworteingabe oder
Schlüsseldatei deklariert; kein Feldname ist fest codiert. Bei Agents sind das das Postfach-Passwort und der geheime
Clientschlüssel (Entra ID) des E-Mail-Agenten, der API-Schlüssel einer Verbindung des MCP-Tool-Agenten und das
Jira-Token des Release-Notes-Assistenten.

- **Verschlüsselt gespeichert**: Die API verschlüsselt ein Geheimnis, bevor sie es speichert, mit dem Schlüssel in
  `AIHUB_CONFIG_ENCRYPTION_KEY`. Die Datenbank, ihre Backups und die Konfiguration, die ein Agent über NATS abruft,
  enthalten nur den Chiffretext.
- **Nur dort entschlüsselt, wo es gebraucht wird**: Ein Agent entschlüsselt seine Geheimnisse erst, wenn er das Profil
  für einen Lauf validiert. Der Laufzustand, den er in Valkey ablegt, enthält den Chiffretext.
- **Maskiert in Antworten**: Die API gibt weder ein Geheimnis noch seinen Chiffretext zurück. Ein gespeichertes
  Geheimnis wird als Maske angezeigt, und wer das Formular mit unveränderter Maske speichert, behält das gespeicherte
  Geheimnis. Eine Maske ist an ihr Feld und ihr Profil gebunden und wird überall sonst abgelehnt.
- **Export, Import und Klonen**: Ein exportiertes Profil enthält Masken, nie Geheimnisse. Beim Import einer solchen
  Datei oder beim Klonen eines Profils werden die maskierten Felder geleert, und die Admin-Oberfläche nennt sie, damit
  Sie sie vor dem Speichern erneut eingeben.

### Der Schlüssel

`AIHUB_CONFIG_ENCRYPTION_KEY` ist ein Fernet-Schlüssel, die URL-sichere Base64-Kodierung von 32 zufälligen Bytes.
Erzeugen Sie einen mit `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`.
Derselbe Schlüssel muss die API, die Wissens-Pipelines und jeden Agenten erreichen, dessen Profile ein Geheimnis
enthalten: `imap_agent`, `email_classification_agent` und `release_notes_agent` in den mitgelieferten Compose-Dateien
sowie jeden eigenen SDK-Agenten, der ein Passwortfeld deklariert.

- **Erforderlich, sobald ein Geheimnis gespeichert ist**: Die API verweigert den Start, solange ein gespeichertes Profil
  ein Geheimnis enthält und der Schlüssel fehlt oder ungültig ist. Profile, die alle Geheimnisse leer lassen, brauchen
  keinen Schlüssel.
- **Keine Rotation**: Ein geänderter Schlüssel macht jedes gespeicherte Geheimnis unlesbar. Geben Sie die Geheimnisse
  nach einem Wechsel erneut ein.
- **Backups sind an den Schlüssel gebunden**: Ein Datenbank-Backup stellt nutzbare Geheimnisse nur zusammen mit dem
  Schlüssel wieder her, der bei seiner Erstellung galt. Bewahren Sie den Schlüssel sicher auf, und getrennt von den
  Backups.

### Upgrade auf verschlüsselte Agent-Geheimnisse

Agent-Profile, die gespeichert wurden, bevor Agent-Geheimnisse verschlüsselt wurden, enthalten sie noch im Klartext; die
API verschlüsselt sie bei ihrem ersten Start. Aktualisieren Sie zuerst die Agent-Container, oder im selben Deployment,
und die API zuletzt: Ein Agent, der nicht entschlüsseln kann, würde den Chiffretext als Zugangsdaten verwenden. Eigene
SDK-Agenten mit Passwortfeldern müssen vor der API aktualisiert werden und den Schlüssel erhalten. Nach dem Upgrade:

- Erneuern Sie die IMAP-, MCP- und Jira-Zugangsdaten. Exporte, Traces und Backups von vor dem Upgrade können sie noch im
  Klartext enthalten.
- Laden Sie jedes Profilformular neu, das während des Upgrades offen war. Das Speichern kann sonst mit der Aufforderung
  abgelehnt werden, das Formular erneut abzusenden.

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
