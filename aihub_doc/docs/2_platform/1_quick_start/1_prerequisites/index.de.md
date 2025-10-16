---
title: Prüfung der Voraussetzungen
index: 1
source_sha: "292f97d6deec3a28647cbc00876305ef435d47e5beeb2e7e4f2bb9aa757e5482"
---

# Voraussetzungen: Vorbereitung für das Deployment der Plattform

Bevor Sie die Swiss AI Hub Plattform deployen, stellen Sie sicher, dass Ihre Infrastruktur die Mindestanforderungen erfüllt und dass Sie die erforderliche Authentifizierung eingerichtet haben. Diese Checkliste gewährleistet ein reibungsloses Deployment-Erlebnis.

## Hardware-Anforderungen

Die Swiss AI Hub Plattform benötigt erhebliche Ressourcen, um alle Komponenten effektiv zu betreiben:

**Mindestanforderungen:**

-   **CPU**: 8 Kerne
-   **RAM**: 32 GB
-   **Speicher**: 200 GB freier Speicherplatz
-   **Netzwerk**: Stabile Internetverbindung für Docker-Image-Downloads

**Empfohlene Spezifikationen:**

-   **CPU**: 12+ Kerne für optimale Leistung
-   **RAM**: 48+ GB für komfortablen Betrieb
-   **Speicher**: 300+ GB mit SSD empfohlen für Datenbankleistung
-   **Netzwerk**: Hochbandbreitenverbindung für schnellere Ersteinrichtung

::: warning Ressourcenauswirkungen
Die Plattform betreibt mehrere Dienste gleichzeitig: Datenbanken (MongoDB, Redis), Vektordatenbanken (Milvus), LLM-Proxy-Server, Web-Interfaces und Verarbeitungs-Engines. Unzureichende Ressourcen führen zu Dienstausfällen oder schlechter Performance.
:::

## Betriebssystem und Software

**Betriebssystem:**

-   **Linux** (Ubuntu 20.04+ empfohlen und getestet)
-   **Docker-kompatible** Linux-Distribution

**Erforderliche Software:**

-   **Docker** (neueste stabile Version)
-   **Docker Compose** (v2.0+)
-   **sudo/root-Zugriff** für Installation und Konfiguration

**Netzwerkkonfiguration:**

-   **Offene Ports**: 80 (HTTP), 443 (HTTPS) und alle benutzerdefinierten Ports für Ihre Konfiguration
-   **Internetzugang** zum Herunterladen von Docker-Images und Updates
-   **Domain-/DNS-Einrichtung**, wenn für externen Zugriff deployed wird

::: tip Installationsüberprüfung
Testen Sie Ihre Docker-Einrichtung:

```bash
docker --version
docker compose --version
docker run hello-world
```

Alle Befehle sollten erfolgreich abgeschlossen werden.
:::

## Einrichtung des Authentifizierungsanbieters

Die Swiss AI Hub Plattform benötigt einen OAuth2/OpenID Connect Identitätsanbieter. Diese Anleitung behandelt die Einrichtung von Azure Entra ID, aber auch andere Anbieter wie Google, Okta oder Auth0 können mit ähnlichen Konfigurationsmustern verwendet werden.

### Azure Entra ID Konfiguration

Befolgen Sie diese Schritte, um die Azure-Authentifizierung einzurichten:

**Schritt 1: App-Registrierung erstellen**

1.  Navigieren Sie zu Azure Portal → Azure Active Directory → App registrations
2.  Klicken Sie auf „New registration“
3.  Konfigurieren Sie die Anwendung:
    -   **Name**: „Swiss AI Hub“ (oder Ihr bevorzugter Name)
    -   **Supported account types**: „Accounts in this organizational directory only“ (oder je nach Bedarf)
    -   **Redirect URI**: Wählen Sie „Web“ und geben Sie ein:
        ```
        https://your-domain.com/oauth/oidc/callback
        ```
        (Ersetzen Sie `your-domain.com` durch Ihre tatsächliche Domain oder verwenden Sie `127.0.0.1.nip.io` für lokale Tests)
4.  Klicken Sie auf „Register“

**Schritt 2: API-Berechtigungen konfigurieren**

1.  Gehen Sie zu „API permissions“ → „Add a permission“
2.  Wählen Sie „Microsoft Graph“ → „Delegated permissions“
3.  Fügen Sie diese Berechtigungen hinzu:
    -   `openid`
    -   `profile`
    -   `email`
    -   `offline_access`
    -   `User.Read`
4.  Wählen Sie „Microsoft Graph“ → „Application permissions“
5.  Fügen Sie diese Berechtigungen hinzu:
    -   `User.ReadBasic.All`
    -   `Directory.Read.All`
    -   `ProfilePhoto.Read.All`
6.  Klicken Sie auf „Grant admin consent for [Your Organization]“

**Schritt 3: Client-Secret erstellen**

1.  Gehen Sie zu „Certificates & secrets“ → „New client secret“
2.  Fügen Sie eine Beschreibung hinzu und legen Sie die Ablaufperiode fest
3.  Klicken Sie auf „Add“ und **kopieren Sie sofort den Secret-Wert** – Sie werden ihn später nicht mehr sehen
4.  Speichern Sie diesen als Ihr `[CLIENT_SECRET]`

**Schritt 4: App-Rollen einrichten**

1.  Gehen Sie zu „App roles“ → „Create app role“
2.  Erstellen Sie eine Rolle für Administratoren:
    -   **Display name**: `AIHubAdmin`
    -   **Allowed member types**: „Users/Groups“
    -   **Value**: `AIHubAdmin`
3.  Erstellen Sie eine Rolle für reguläre Benutzer:
    -   **Display name**: `AIHubUser`
    -   **Allowed member types**: „Users/Groups“
    -   **Value**: `AIHubUser`

**Schritt 5: SPA-Authentifizierung konfigurieren**

1.  Gehen Sie zu „Authentication“ → „Add a platform“ → „Single-page application“
2.  Fügen Sie diese Redirect-URIs hinzu (ersetzen Sie die Domain bei Bedarf):
    ```
    https://your-domain.com/de/auth/callback
    https://your-domain.com/en/auth/callback
    https://your-domain.com/it/auth/callback
    https://your-domain.com/fr/auth/callback
    ```
3.  Klicken Sie auf „Save“

**Schritt 6: Konfigurationswerte sammeln**

Kopieren Sie von der „Overview“-Seite Ihrer App-Registrierung diese Werte:

-   **Application (client) ID** → Speichern Sie als `[CLIENT_ID]`
-   **Directory (tenant) ID** → Speichern Sie als `[TENANT_ID]`

### Erforderliche Authentifizierungsinformationen

Nach Abschluss der Azure-Einrichtung sollten Sie über Folgendes verfügen:

-   `[CLIENT_ID]` - Application (client) ID
-   `[CLIENT_SECRET]` - Client secret value
-   `[TENANT_ID]` - Directory (tenant) ID

Sie benötigen diese Werte während der Konfiguration für das Deployment der Plattform.
