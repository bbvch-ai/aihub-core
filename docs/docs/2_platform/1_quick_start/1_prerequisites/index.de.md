---
title: Voraussetzungen
source_sha: 88eadf51293b9e1777d3ab7fdaab495683f76c2c7d682f5c0e3f38346314ade8
---

# Voraussetzungen

Dieser Leitfaden behandelt die Voraussetzungen für das Deployment der Swiss AI Hub Plattform.

::: tip Wählen Sie Ihren Deployment-Typ
Die Voraussetzungen unterscheiden sich je nach Ihrem Deployment-Typ:

- **Produktions-Deployment**: Deployment auf einem Server mit einem echten Domainnamen und automatischen
  SSL-Zertifikaten
- **Lokales Deployment**: Ausführung auf Ihrer lokalen Maschine mit `127.0.0.1.nip.io` und selbstsignierten Zertifikaten

Folgen Sie nur den Abschnitten, die für Ihren Deployment-Typ relevant sind.
:::

## Allgemeine Anforderungen (Alle Deployments)

Diese Anforderungen gelten sowohl für Produktions- als auch für lokale Deployments.

### Systemanforderungen

#### Mindestanforderungen

- **CPU**: 8 Kerne
- **RAM**: 32 GB
- **Speicherplatz**: 200 GB freier Speicherplatz
- **Netzwerk**: Stabile Internetverbindung für Docker-Image-Downloads

#### Empfohlene Spezifikationen

- **CPU**: 12+ Kerne
- **RAM**: 48+ GB
- **Speicherplatz**: 300+ GB SSD für verbesserte Datenbankleistung
- **Netzwerk**: Hochbandbreitenverbindung für schnellere Erstinbetriebnahme

::: warning
Die Plattform betreibt mehrere Services gleichzeitig (Datenbanken, Vektorspeicher, LLM-Proxys, Weboberflächen,
Verarbeitungs-Engines). Systeme unterhalb der Mindestanforderungen werden Serviceausfälle oder eine verschlechterte
Leistung erfahren.
:::

### Softwareanforderungen

#### Betriebssystem

- Linux (Ubuntu 20.04+ empfohlen und getestet)
- Jede Docker-kompatible Linux-Distribution

#### Erforderliche Software

- **Docker**: Neueste stabile Version
- **Docker Compose**: v2.0 oder höher
- **sudo/root-Zugriff**: Erforderlich für Installation und Konfiguration

#### Netzwerkkonfiguration

- **Offene Ports**: 80 (HTTP), 443 (HTTPS)
- **Internetzugang**: Erforderlich für Docker-Image-Downloads und Updates

#### Verifikation

Testen Sie Ihre Docker-Installation:

```bash
docker --version
docker compose --version
docker run hello-world
```

Alle Befehle müssen erfolgreich abgeschlossen werden.

### Einrichtung des Authentifizierungs-Providers

Die Plattform erfordert einen OAuth2/OpenID Connect Identitätsprovider sowohl für Produktions- als auch für lokale
Deployments. Dieser Leitfaden beschreibt die Einrichtung von Azure Entra ID. Andere Provider (Google, Okta, Auth0)
können mit ähnlichen Mustern konfiguriert werden.

#### Azure Entra ID Einrichtung

Führen Sie die folgenden Schritte im Azure-Portal aus, um die Authentifizierung vorzubereiten:

**Schritt 1: App-Registrierung erstellen**

1. Navigieren Sie zu **Azure-Portal** → **Azure Active Directory** → **App-Registrierungen**
2. Klicken Sie auf **"Neue Registrierung"**
3. Konfigurieren Sie die Registrierung:
   - **Name**: `Swiss AI Hub` (oder die Namenskonvention Ihrer Organisation)
   - **Unterstützte Kontotypen**: Wählen Sie basierend auf den Anforderungen
     - `Konten nur in diesem Organisationsverzeichnis` (Single Tenant – empfohlen für die meisten Deployments)
   - **Umleitungs-URI**: Leer lassen (wird in Schritt 5 konfiguriert)
4. Klicken Sie auf **"Registrieren"**

**Schritt 2: Token-Version konfigurieren**

Die Plattform erfordert Access Token Version 2 für eine ordnungsgemäße Authentifizierung.

1. Navigieren Sie zu **"Manifest"**
2. Suchen Sie die Eigenschaft `requestedAccessTokenVersion`
3. Ändern Sie den Wert von `null` oder `1` auf `2`:
   ```json
   "requestedAccessTokenVersion": 2
   ```
4. Klicken Sie auf **"Speichern"** oben im Manifest-Editor

::: warning
Access Token Version 2 ist für die ordnungsgemäße Funktion der Plattform erforderlich. Version 1 Tokens werden nicht
unterstützt und führen zu Authentifizierungsfehlern.
:::

**Schritt 3: API-Berechtigungen konfigurieren**

1. Navigieren Sie zu **"API-Berechtigungen"** → **"Eine Berechtigung hinzufügen"**
2. Wählen Sie **"Microsoft Graph"** → **"Delegierte Berechtigungen"**
3. Fügen Sie die folgenden Berechtigungen hinzu:
   - `openid` - Erforderlich für OpenID Connect-Authentifizierung
   - `profile` - Erforderlich für grundlegende Benutzerprofilinformationen
   - `email` - Erforderlich für die E-Mail-Adresse
   - `offline_access` - Erforderlich für Refresh Tokens
   - `User.Read` - Erforderlich zum Lesen des Benutzerprofils
4. Klicken Sie auf **"Administratorzustimmung für [Ihre Organisation] erteilen"**
5. Verifizieren Sie, dass alle Berechtigungen den Status **"Erteilt für [Ihre Organisation]"** anzeigen

::: tip
Die Plattform verwaltet Rollen und Benutzerprofile lokal – es sind keine Microsoft Graph API Anwendungsberechtigungen
(wie `User.ReadBasic.All`, `Directory.Read.All` oder `ProfilePhoto.Read.All`) erforderlich. Nur standardmäßige OIDC
delegierte Berechtigungen werden für die Authentifizierung benötigt.
:::

**Schritt 4: Client Secret erstellen**

1. Navigieren Sie zu **"Zertifikate & Geheimnisse"** → **"Client-Geheimnisse"** → **"Neues Client-Geheimnis"**
2. Konfigurieren Sie das Geheimnis:
   - **Beschreibung**: Geben Sie einen aussagekräftigen Namen ein (z. B. `Swiss AI Hub Secret`)
   - **Läuft ab**: Wählen Sie die Ablaufperiode (12-24 Monate empfohlen)
3. Klicken Sie auf **"Hinzufügen"**
4. **Kopieren Sie den geheimen Wert sofort** in einen sicheren Speicher
5. Notieren Sie diesen Wert als `[CLIENT_SECRET]` für die Deployment-Konfiguration

::: danger
Der Client Secret Wert wird nur einmal unmittelbar nach der Erstellung angezeigt. Geht der Wert verloren, muss ein neues
Geheimnis erstellt werden. Speichern Sie es in einem Passwort-Manager oder einem sicheren Tresor.
:::

**Schritt 5: App-Rollen konfigurieren (optional)**

::: tip
App-Rollen in Azure Entra ID sind für die Swiss AI Hub Plattform **optional**. Plattform-Rollen (AIHubAdmin, AIHubUser)
werden lokal über die Admin-Oberfläche verwaltet, nicht vom Identitätsprovider synchronisiert. Diese Azure App-Rollen
sind nur dann erforderlich, wenn Sie den Zugriff auf integrierte Services (Dagster, SeaweedFS, Attu) steuern möchten,
die ihre eigenen OAuth2-Flows verwenden.
:::

Erstellen Sie vier App-Rollen nach diesem Prozess:

1. Navigieren Sie zu **"App-Rollen"** → **"App-Rolle erstellen"**
2. Erstellen Sie jede der folgenden Rollen:

**Administrator-Rolle:**

- **Anzeigename**: `AIHubAdmin`
- **Zulässige Mitgliedstypen**: `Benutzer/Gruppen`
- **Wert**: `AIHubAdmin`
- **Beschreibung**: `Administratorzugriff auf die Swiss AI Hub Plattform`

**Benutzer-Rolle:**

- **Anzeigename**: `AIHubUser`
- **Zulässige Mitgliedstypen**: `Benutzer/Gruppen`
- **Wert**: `AIHubUser`
- **Beschreibung**: `Standard-Benutzerzugriff auf die Swiss AI Hub Plattform`

**Developer-Rolle:**

- **Anzeigename**: `AIHubDeveloper`
- **Zulässige Mitgliedstypen**: `Benutzer/Gruppen`
- **Wert**: `AIHubDeveloper`
- **Beschreibung**: `Entwicklerzugriff auf Swiss AI Hub Plattform-Services`

**Systemadministrator-Rolle:**

- **Anzeigename**: `AIHubSysAdmin`
- **Zulässige Mitgliedstypen**: `Benutzer/Gruppen`
- **Wert**: `AIHubSysAdmin`
- **Beschreibung**: `Systemadministrator-Zugriff auf Infrastruktur-Tools (Dagster, SeaweedFS, Attu)`

::: tip
Die Rolle `AIHubSysAdmin` ist erforderlich, um auf das Dagster Pipeline Orchestrierungs-Dashboard, die SeaweedFS Data
Lake Konsole unter `datalake.${DOMAIN}` und die Attu Milvus Admin-UI zuzugreifen. Benutzer ohne diese Rolle können
weiterhin die Haupt-Swiss AI Hub Oberfläche und OpenWebUI nutzen.
:::

**Schritt 6: SPA-Umleitungs-URIs konfigurieren**

Single-Page Application (SPA) Umleitungs-URIs sind für die Hauptweboberfläche mit mehrsprachiger Unterstützung
erforderlich.

1. Navigieren Sie zu **"Authentifizierung"** → **"Eine Plattform hinzufügen"** → **"Single-Page-Anwendung"**

2. Fügen Sie Umleitungs-URIs basierend auf Ihrem Deployment-Typ hinzu:

   **Für die Produktion:** Ersetzen Sie `your-domain.com` durch Ihre tatsächliche Domain

   ```
   https://your-domain.com/de/auth/callback
   https://your-domain.com/en/auth/callback
   https://your-domain.com/it/auth/callback
   https://your-domain.com/fr/auth/callback
   ```

   **Für lokales Deployment:** Verwenden Sie `127.0.0.1.nip.io`

   ```
   https://127.0.0.1.nip.io/de/auth/callback
   https://127.0.0.1.nip.io/en/auth/callback
   https://127.0.0.1.nip.io/it/auth/callback
   https://127.0.0.1.nip.io/fr/auth/callback
   ```

   ::: tip
Sie können für Testzwecke sowohl Produktions- als auch lokale URIs derselben App-Registrierung hinzufügen.
   :::

3. Konfigurieren Sie die Token-Einstellungen:
   - Aktivieren Sie **Access Tokens** (für implizite Flows verwendet)
   - Aktivieren Sie **ID Tokens** (für implizite Flows verwendet)
4. Klicken Sie auf **"Konfigurieren"**

**Schritt 7: Webanwendungs-Umleitungs-URIs konfigurieren**

Webanwendungs-Umleitungs-URIs sind für integrierte Services (OpenWebUI, Dagster, Data Lake) erforderlich.

1. Navigieren Sie zu **"Authentifizierung"** → **"Eine Plattform hinzufügen"** → **"Web"**

2. Fügen Sie Umleitungs-URIs basierend auf Ihrem Deployment-Typ hinzu:

   **Für die Produktion:** Ersetzen Sie `your-domain.com` durch Ihre tatsächliche Domain

   ```
   https://openwebui.your-domain.com/oauth/oidc/callback
   https://dagster.your-domain.com/oauth2/callback
   https://datalake.your-domain.com/oauth2/callback
   https://attu.your-domain.com/oauth2/callback
   ```

   **Für lokales Deployment:** Verwenden Sie `127.0.0.1.nip.io`

   ```
   https://openwebui.127.0.0.1.nip.io/oauth/oidc/callback
   https://dagster.127.0.0.1.nip.io/oauth2/callback
   https://datalake.127.0.0.1.nip.io/oauth2/callback
   https://attu.127.0.0.1.nip.io/oauth2/callback
   ```

3. Konfigurieren Sie die Token-Einstellungen:

   - Aktivieren Sie **ID Tokens** (für hybride Flows verwendet)

4. Klicken Sie auf **"Konfigurieren"**

::: warning Plattformtyp-Unterscheidung
Die Plattformtyp-Konfiguration (SPA vs. Web) ist entscheidend für die OAuth2-Flow-Auswahl:

- **SPA-Plattform**: Sprachspezifische Callbacks (`/de/`, `/en/`, `/fr/`, `/it/`) verwenden den PKCE-Flow ohne Client
  Secret
- **Web-Plattform**: Service-Callbacks (`openwebui`, `dagster`, `datalake`, `attu`) verwenden den
  Autorisierungscode-Flow mit Client Secret

Falsch konfigurierte Plattformtypen führen zum Authentifizierungsfehler
`AADSTS9002326: Cross-origin token redemption is permitted only for the 'Single-Page Application' client-type`. Stellen
Sie sicher, dass die Umleitungs-URIs unter dem korrekten Plattformtyp registriert sind.
:::

**Erforderliche Authentifizierungsinformationen**

Nach Abschluss der Azure-Einrichtung sollten Sie über Folgendes verfügen:

- `[CLIENT_ID]` - Anwendungs-(Client-)ID
- `[CLIENT_SECRET]` - Client Secret Wert
- `[TENANT_ID]` - Verzeichnis-(Tenant-)ID

Sie benötigen diese Werte während der Plattform-Deployment-Konfiguration.

______________________________________________________________________

## Voraussetzungen für das Produktions-Deployment

::: danger Nur für Produktions-Deployments
**Überspringen Sie diesen gesamten Abschnitt, wenn Sie lokal testen.** Diese Schritte sind nur erforderlich, wenn Sie
auf einem Server mit einem echten Domainnamen deployen.
:::

### DNS-Konfiguration

Konfigurieren Sie DNS-Einträge für Ihre Domain. Die Plattform erfordert **sieben Subdomains**, die auf die öffentliche
IP-Adresse Ihres Servers zeigen:

- `swiss-ai-hub.example.com` - Haupt-Weboberfläche
- `openwebui.swiss-ai-hub.example.com` - Chat-UI
- `dagster.swiss-ai-hub.example.com` - Pipeline-Orchestrierung
- `datalake.swiss-ai-hub.example.com` - Data Lake Konsole
- `litellm.swiss-ai-hub.example.com` - Litellm-Proxy
- `attu.swiss-ai-hub.example.com` - Milvus Vektordatenbank-UI
- `traefik.swiss-ai-hub.example.com` - Reverse Proxy Dashboard

Ersetzen Sie `swiss-ai-hub.example.com` durch Ihre tatsächliche Domain. Erstellen Sie A-Einträge oder CNAMEs für alle
sieben Subdomains, die auf die IP-Adresse Ihres Servers zeigen.

::: warning DNS-Anforderungen für SSL
- DNS-Einträge müssen für die Bereitstellung von Let's Encrypt SSL-Zertifikaten global zugänglich sein
- Die VM muss ihre eigenen Domainnamen auflösen können (interne DNS-Auflösung)
- Konfigurieren Sie die Nameserver korrekt, um OAuth-Authentifizierungs-Timeouts zu vermeiden

Siehe [Netzwerkanforderungen](../../3_deployment_guide/7_network_requirements/) für detaillierte DNS-Konfiguration und
Fehlerbehebung.
:::

______________________________________________________________________

## Voraussetzungen für lokales Deployment

::: danger Nur für lokales Deployment
**Überspringen Sie diesen gesamten Abschnitt, wenn Sie in der Produktion deployen.** Diese Schritte sind nur
erforderlich, wenn Sie die Plattform auf Ihrer lokalen Maschine deployen.
:::

### mkcert installieren

Für lokales Deployment mit HTTPS-Unterstützung müssen Sie **mkcert** installieren, um selbstsignierte SSL-Zertifikate zu
generieren, die von Ihrem Browser als vertrauenswürdig eingestuft werden.

::: warning
Verwenden Sie selbstsignierte SSL-Zertifikate nur für die lokale Entwicklung. Verwenden Sie diese niemals in
Produktions- oder öffentlichen Umgebungen.
:::

**Linux (Ubuntu/Debian):**

```bash
sudo apt install libnss3-tools
wget -O mkcert https://dl.filippo.io/mkcert/latest?for=linux/amd64
chmod +x mkcert
sudo mv mkcert /usr/local/bin/
```

**Windows:**

```powershell
# Using Chocolatey
choco install mkcert

# OR using Scoop
scoop bucket add extras
scoop install mkcert
```

**macOS:**

```bash
brew install mkcert
```

**Installation verifizieren:**

```bash
mkcert -version
```

::: tip Was ist mkcert?
**mkcert** ist ein Tool, das lokal vertrauenswürdige SSL-Zertifikate ohne komplexe Konfiguration generiert. Es
installiert automatisch eine lokale Zertifizierungsstelle (CA) in Ihrem System-Vertrauensspeicher, sodass die von ihm
generierten Zertifikate von Ihrem Browser als vertrauenswürdig eingestuft werden.
:::

______________________________________________________________________

## Nächste Schritte

Fahren Sie mit dem [One-Command Deployment](../2_one_command_deployment/) fort, um die Plattform mit den aufgezeichneten
Konfigurationswerten zu deployen.
