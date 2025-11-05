---
title: Voraussetzungen-Check
source_sha: d101c3600327ac035af09f3c472868fcb856d7a74594ad033bc87ec7e30f9fd5
---

# Voraussetzungen: Vorbereitung für die Plattformbereitstellung

Bevor Sie die Swiss AI Hub Plattform bereitstellen, stellen Sie sicher, dass Ihre Infrastruktur die Mindestanforderungen
erfüllt und dass Sie die notwendige Authentifizierung eingerichtet haben. Diese Checkliste gewährleistet eine
reibungslose Bereitstellung.

## Hardware-Anforderungen

Die Swiss AI Hub Plattform benötigt erhebliche Ressourcen, um alle Komponenten effektiv zu betreiben:

**Mindestanforderungen:**

- **CPU**: 8 Kerne
- **RAM**: 32 GB
- **Speicher**: 200 GB freier Speicherplatz
- **Netzwerk**: Stabile Internetverbindung für Docker-Image-Downloads

**Empfohlene Spezifikationen:**

- **CPU**: 12+ Kerne für optimale Leistung
- **RAM**: 48+ GB für komfortablen Betrieb
- **Speicher**: 300+ GB mit SSD empfohlen für die Datenbankleistung
- **Netzwerk**: Hochbandbreitenverbindung für schnellere Erstinstallation

::: warning Ressourcenauswirkungen
Die Plattform betreibt mehrere Dienste gleichzeitig: Datenbanken (MongoDB, Redis), Vektordatenbanken (Milvus),
LLM-Proxyserver, Weboberflächen und Verarbeitungs-Engines. Unzureichende Ressourcen führen zu Dienstausfällen oder
schlechter Leistung.
:::

## Betriebssystem und Software

**Betriebssystem:**

- **Linux** (Ubuntu 20.04+ empfohlen und getestet)
- **Docker-kompatible** Linux-Distribution

**Erforderliche Software:**

- **Docker** (neueste stabile Version)
- **Docker Compose** (v2.0+)
- **sudo/root-Zugriff** für Installation und Konfiguration

**Netzwerkkonfiguration:**

- **Offene Ports**: 80 (HTTP), 443 (HTTPS) und alle benutzerdefinierten Ports für Ihre Konfiguration
- **Internetzugang** zum Herunterladen von Docker-Images und Updates
- **Domain-/DNS-Einrichtung**, falls für externen Zugriff bereitgestellt wird

::: tip Installationsprüfung
Testen Sie Ihre Docker-Installation:

```bash
docker --version
docker compose --version
docker run hello-world
```

Alle Befehle sollten erfolgreich abgeschlossen werden.
:::

## Einrichtung des Authentifizierungsanbieters

Die Swiss AI Hub Plattform benötigt einen OAuth2/OpenID Connect Identitätsanbieter. Diese Anleitung behandelt die
Einrichtung von Azure Entra ID, aber andere Anbieter wie Google, Okta oder Auth0 können mit ähnlichen
Konfigurationsmustern verwendet werden.

### Azure Entra ID Konfiguration

Befolgen Sie diese Schritte, um die Azure-Authentifizierung einzurichten:

**Schritt 1: App-Registrierung erstellen**

1. Navigieren Sie zu Azure Portal → Azure Active Directory → App-Registrierungen
2. Klicken Sie auf „Neue Registrierung“
3. Konfigurieren Sie die Anwendung:
   - **Name**: „Swiss AI Hub“ (oder Ihr bevorzugter Name)
   - **Unterstützte Kontotypen**: „Nur Konten in diesem Organisationsverzeichnis“ (oder nach Bedarf)
   - **Weiterleitungs-URI**: Wählen Sie „Web“ und geben Sie ein:
     ```
     https://your-domain.com/oauth/oidc/callback
     ```
     (Ersetzen Sie `your-domain.com` durch Ihre tatsächliche Domain oder verwenden Sie `127.0.0.1.nip.io` für lokale
     Tests)
4. Klicken Sie auf „Registrieren“

**Schritt 2: API-Berechtigungen konfigurieren**

1. Gehen Sie zu „API-Berechtigungen“ → „Berechtigung hinzufügen“
2. Wählen Sie „Microsoft Graph“ → „Delegierte Berechtigungen“
3. Fügen Sie diese Berechtigungen hinzu:
   - `openid`
   - `profile`
   - `email`
   - `offline_access`
   - `User.Read`
4. Wählen Sie „Microsoft Graph“ → „Anwendungsberechtigungen“
5. Fügen Sie diese Berechtigungen hinzu:
   - `User.ReadBasic.All`
   - `Directory.Read.All`
   - `ProfilePhoto.Read.All`
6. Klicken Sie auf „Administratorzustimmung für [Ihre Organisation] erteilen“

**Schritt 3: Client-Geheimnis erstellen**

1. Gehen Sie zu „Zertifikate & Geheimnisse“ → „Neues Client-Geheimnis“
2. Fügen Sie eine Beschreibung hinzu und legen Sie die Ablaufzeit fest
3. Klicken Sie auf „Hinzufügen“ und **kopieren Sie sofort den geheimen Wert** – Sie werden ihn später nicht mehr sehen
4. Speichern Sie dies als Ihr `[CLIENT_SECRET]`

**Schritt 4: App-Rollen einrichten**

1. Gehen Sie zu „App-Rollen“ → „App-Rolle erstellen“
2. Erstellen Sie eine Rolle für Administratoren:
   - **Anzeigename**: `AIHubAdmin`
   - **Zulässige Mitgliedstypen**: „Benutzer/Gruppen“
   - **Wert**: `AIHubAdmin`
3. Erstellen Sie eine Rolle für normale Benutzer:
   - **Anzeigename**: `AIHubUser`
   - **Zulässige Mitgliedstypen**: „Benutzer/Gruppen“
   - **Wert**: `AIHubUser`

**Schritt 5: SPA-Authentifizierung konfigurieren**

1. Gehen Sie zu „Authentifizierung“ → „Plattform hinzufügen“ → „Single-Page-Anwendung“
2. Fügen Sie diese Weiterleitungs-URIs hinzu (Domain bei Bedarf ersetzen):
   ```
   https://your-domain.com/de/auth/callback
   https://your-domain.com/en/auth/callback
   https://your-domain.com/it/auth/callback
   https://your-domain.com/fr/auth/callback
   ```
3. Klicken Sie auf „Speichern“

**Schritt 6: Konfigurationswerte sammeln**

Kopieren Sie von der „Übersicht“-Seite Ihrer App-Registrierung diese Werte:

- **Anwendungs-(Client-)ID** → Speichern als `[CLIENT_ID]`
- **Verzeichnis-(Tenant-)ID** → Speichern als `[TENANT_ID]`

### Erforderliche Authentifizierungsinformationen

Nach Abschluss der Azure-Einrichtung sollten Sie über Folgendes verfügen:

- `[CLIENT_ID]` - Anwendungs-(Client-)ID
- `[CLIENT_SECRET]` - Client-Geheimniswert
- `[TENANT_ID]` - Verzeichnis-(Tenant-)ID

Sie benötigen diese Werte während der Konfiguration der Plattformbereitstellung.
