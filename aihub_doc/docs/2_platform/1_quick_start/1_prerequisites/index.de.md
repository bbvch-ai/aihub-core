---
title: Voraussetzungen
source_sha: "0b188ec77305fd1ddfa05ae547e646ac52da75ab3bac73d8d37169977222fd31"
---

# Voraussetzungen

Dieser Leitfaden behandelt die Voraussetzungen für das Deployment der AI-Hub Plattform.

::: tip Wählen Sie Ihren Deployment-Typ
Die Voraussetzungen unterscheiden sich je nach Deployment-Typ:

- **Produktions-Deployment**: Deployment auf einen Server mit einem echten Domainnamen und automatischen SSL-Zertifikaten
- **Lokales Deployment**: Ausführung auf Ihrer lokalen Maschine mit `127.0.0.1.nip.io` und selbstsignierten Zertifikaten

Befolgen Sie nur die Abschnitte, die für Ihren Deployment-Typ relevant sind.
:::

## Allgemeine Anforderungen (Alle Deployments)

Diese Anforderungen gelten sowohl für Produktions- als auch für lokale Deployments.

### Systemanforderungen

#### Mindestanforderungen

- **CPU**: 8 Kerne
- **RAM**: 32 GB
- **Speicher**: 200 GB freier Speicherplatz
- **Netzwerk**: Stabile Internetverbindung für Docker-Image-Downloads

#### Empfohlene Spezifikationen

- **CPU**: 12+ Kerne
- **RAM**: 48+ GB
- **Speicher**: 300+ GB SSD für verbesserte Datenbankleistung
- **Netzwerk**: Hochbandbreitenverbindung für eine schnellere Ersteinrichtung

::: warning
Die Plattform betreibt mehrere Services gleichzeitig (Datenbanken, Vektorspeicher, LLM-Proxys, Weboberflächen,
Verarbeitungs-Engines). Systeme unterhalb der Mindestanforderungen werden Servicefehler oder eine verminderte Leistung aufweisen.
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

#### Verifizierung

Testen Sie Ihre Docker-Installation:

```bash
docker --version
docker compose --version
docker run hello-world
```

Alle Befehle müssen erfolgreich abgeschlossen werden.

### Einrichtung des Authentifizierungsanbieters

Die Plattform benötigt einen OAuth2/OpenID Connect Identity Provider für sowohl Produktions- als auch lokale Deployments.
Dieser Leitfaden dokumentiert die Einrichtung von Azure Entra ID. Andere Provider (Google, Okta, Auth0) können
nach ähnlichen Mustern konfiguriert werden.

#### Azure Entra ID Einrichtung

Führen Sie die folgenden Schritte im Azure Portal aus, um die Authentifizierung vorzubereiten:

**Schritt 1: App-Registrierung erstellen**

1. Navigieren Sie zu **Azure Portal** → **Azure Active Directory** → **App-Registrierungen**
2. Klicken Sie auf **"Neue Registrierung"**
3. Konfigurieren Sie die Registrierung:
   - **Name**: `Swiss AI Hub` (oder die Namenskonvention Ihrer Organisation)
   - **Unterstützte Kontotypen**: Wählen Sie basierend auf den Anforderungen
     - `Konten nur in diesem Organisationsverzeichnis` (Single-Tenant — empfohlen für die meisten Deployments)
   - **Umleitungs-URI**: Leer lassen (wird in Schritt 5 konfiguriert)
4. Klicken Sie auf **"Registrieren"**

**Schritt 2: Token-Version konfigurieren**

Die Plattform erfordert Access Token Version 2 für die ordnungsgemäße Authentifizierung.

1. Navigieren Sie zu **"Manifest"**
2. Suchen Sie die Eigenschaft `requestedAccessTokenVersion`
3. Ändern Sie den Wert von `null` oder `1` auf `2`:
   ```json
   "requestedAccessTokenVersion": 2
   ```
4. Klicken Sie oben im Manifest-Editor auf **"Speichern"**

::: warning
Access Token Version 2 ist erforderlich, damit die Plattform korrekt funktioniert. Version 1 Token werden nicht
unterstützt und führen zu Authentifizierungsfehlern.
:::

**Schritt 3: API-Berechtigungen konfigurieren**

1. Navigieren Sie zu **"API-Berechtigungen"** → **"Berechtigung hinzufügen"**
2. Wählen Sie **"Microsoft Graph"** → **"Delegierte Berechtigungen"**
3. Fügen Sie die folgenden Berechtigungen hinzu:
   - `openid` - Erforderlich für OpenID Connect-Authentifizierung
   - `profile` - Erforderlich für grundlegende Benutzerprofilinformationen
   - `email` - Erforderlich für die E-Mail-Adresse
   - `offline_access` - Erforderlich für Refresh Tokens
   - `User.Read` - Erforderlich für das Lesen von Benutzerprofilen
   - `Group.Read.All` - Erforderlich für Gruppenmitgliedschaftsinformationen
4. Wählen Sie **"Microsoft Graph"** → **"Anwendungsberechtigungen"**
5. Fügen Sie die folgenden Berechtigungen hinzu:
   - `User.ReadBasic.All` - Erforderlich zum Lesen der grundlegenden Profile aller Benutzer
   - `Directory.Read.All` - Erforderlich zum Lesen von Verzeichnisdaten
   - `ProfilePhoto.Read.All` - Erforderlich zum Lesen von Profilfotos
6. Klicken Sie auf **"Administratorzustimmung für [Ihre Organisation] erteilen"**
7. Überprüfen Sie, ob alle Berechtigungen den Status **"Für [Ihre Organisation] erteilt"** anzeigen

::: warning
Alle aufgeführten Berechtigungen sind für die Funktionalität der Plattform erforderlich. Fehlende Berechtigungen führen
während des Deployments zu Authentifizierungs- oder Autorisierungsfehlern.
:::

**Schritt 4: Client-Geheimnis erstellen**

1. Navigieren Sie zu **"Zertifikate & Geheimnisse"** → **"Client-Geheimnisse"** → **"Neues Client-Geheimnis"**
2. Konfigurieren Sie das Geheimnis:
   - **Beschreibung**: Geben Sie einen aussagekräftigen Namen ein (z.B. `AI-Hub Secret`)
   - **Läuft ab**: Wählen Sie den Ablaufzeitraum (12-24 Monate empfohlen)
3. Klicken Sie auf **"Hinzufügen"**
4. **Kopieren Sie sofort den Geheimniswert** in einen sicheren Speicher
5. Notieren Sie diesen Wert als `[CLIENT_SECRET]` für die Deployment-Konfiguration

::: danger
Der Client-Geheimniswert wird nur einmal direkt nach der Erstellung angezeigt. Geht der Wert verloren, muss ein neues
Geheimnis erstellt werden. Speichern Sie ihn in einem Passwort-Manager oder einem sicheren Tresor.
:::

**Schritt 5: App-Rollen konfigurieren**

App-Rollen ermöglichen die rollenbasierte Zugriffskontrolle (RBAC) für Plattformbenutzer.

Erstellen Sie drei App-Rollen nach diesem Prozess:

1. Navigieren Sie zu **"App-Rollen"** → **"App-Rolle erstellen"**
2. Erstellen Sie jede der folgenden Rollen:

**Administratorrolle:**

- **Anzeigename**: `AIHubAdmin`
- **Zulässige Mitgliedstypen**: `Benutzer/Gruppen`
- **Wert**: `AIHubAdmin`
- **Beschreibung**: `Administratorzugriff auf die AI-Hub Plattform`

**Benutzerrolle:**

- **Anzeigename**: `AIHubUser`
- **Zulässige Mitgliedstypen**: `Benutzer/Gruppen`
- **Wert**: `AIHubUser`
- **Beschreibung**: `Standard-Benutzerzugriff auf die AI-Hub Plattform`

**Entwicklerrolle:**

- **Anzeigename**: `AIHubDeveloper`
- **Zulässige Mitgliedstypen**: `Benutzer/Gruppen`
- **Wert**: `AIHubDeveloper`
- **Beschreibung**: `Entwicklerzugriff auf AI-Hub Plattform-Services (Dagster, SeaweedFS Data Lake Konsole)`

::: tip
Die Rolle `AIHubDeveloper` ist erforderlich, um auf das Dagster Pipeline Orchestrierungs-Dashboard und die SeaweedFS Data Lake Konsole unter `datalake.${DOMAIN}` zuzugreifen. Benutzer ohne diese Rolle können die Haupt-AI-Hub-Oberfläche und OpenWebUI weiterhin nutzen.
:::

**Schritt 6: SPA-Umleitungs-URIs konfigurieren**

Single-Page Application (SPA) Umleitungs-URIs sind für die Hauptweboberfläche mit mehrsprachiger Unterstützung erforderlich.

1. Navigieren Sie zu **"Authentifizierung"** → **"Plattform hinzufügen"** → **"Single-Page-Anwendung"**

2. Fügen Sie Umleitungs-URIs basierend auf Ihrem Deployment-Typ hinzu:

   **Für Produktion:** Ersetzen Sie `your-domain.com` durch Ihre tatsächliche Domain

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
Sie können sowohl Produktions- als auch lokale URIs für Testzwecke zur selben App-Registrierung hinzufügen.
   :::

3. Token-Einstellungen konfigurieren:
   - **Zugriffstoken** aktivieren (für implizite Flows verwendet)
   - **ID-Token** aktivieren (für implizite Flows verwendet)
4. Klicken Sie auf **"Konfigurieren"**

**Schritt 7: Webanwendungs-Umleitungs-URIs konfigurieren**

Webanwendungs-Umleitungs-URIs sind für integrierte Services (OpenWebUI, Dagster, Data Lake) erforderlich.

1. Navigieren Sie zu **"Authentifizierung"** → **"Plattform hinzufügen"** → **"Web"**

2. Fügen Sie Umleitungs-URIs basierend auf Ihrem Deployment-Typ hinzu:

   **Für Produktion:** Ersetzen Sie `your-domain.com` durch Ihre tatsächliche Domain

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

3. Token-Einstellungen konfigurieren:

   - **ID-Token** aktivieren (für hybride Flows verwendet)

4. Klicken Sie auf **"Konfigurieren"**

::: warning Unterscheidung nach Plattformtyp
Die Konfiguration des Plattformtyps (SPA vs. Web) ist entscheidend für die Auswahl des OAuth2-Flows:

- **SPA-Plattform**: Sprachspezifische Callbacks (`/de/`, `/en/`, `/fr/`, `/it/`) verwenden den PKCE-Flow ohne Client-Geheimnis
- **Web-Plattform**: Service-Callbacks (`openwebui`, `dagster`, `datalake`, `attu`) verwenden den Authorization Code Flow mit Client-Geheimnis

Fehlkonfigurierte Plattformtypen führen zu Authentifizierungsfehlern:
`AADSTS9002326: Cross-origin token redemption is permitted only for the 'Single-Page Application' client-type`. Stellen Sie
sicher, dass Umleitungs-URIs unter dem korrekten Plattformtyp registriert sind.
:::

**Erforderliche Authentifizierungsinformationen**

Nach Abschluss der Azure-Einrichtung sollten Sie über Folgendes verfügen:

- `[CLIENT_ID]` - Anwendungs- (Client-) ID
- `[CLIENT_SECRET]` - Client-Geheimniswert
- `[TENANT_ID]` - Verzeichnis- (Tenant-) ID

Sie benötigen diese Werte während der Konfiguration des Plattform-Deployments.

---

## Voraussetzungen für Produktions-Deployments

::: danger Nur für Produktions-Deployments
**Überspringen Sie diesen gesamten Abschnitt, wenn Sie lokal testen.** Diese Schritte sind nur erforderlich, wenn Sie auf
einem Server mit einem echten Domainnamen deployen.
:::

### DNS-Konfiguration

Konfigurieren Sie DNS-Einträge für Ihre Domain. Die Plattform benötigt **sieben Subdomains**, die auf die öffentliche IP-Adresse Ihres Servers zeigen:

- `aihub.example.com` - Haupt-Weboberfläche
- `openwebui.aihub.example.com` - Chat-UI
- `dagster.aihub.example.com` - Pipeline-Orchestrierung
- `datalake.aihub.example.com` - Data Lake-Konsole
- `litellm.aihub.example.com` - LiteLLM-Proxy
- `attu.aihub.example.com` - Milvus-Vektordatenbank-UI
- `traefik.aihub.example.com` - Reverse Proxy Dashboard

Ersetzen Sie `aihub.example.com` durch Ihre tatsächliche Domain. Erstellen Sie A-Records oder CNAMEs für alle sieben Subdomains, die auf die IP-Adresse Ihres Servers zeigen.

::: warning DNS-Anforderungen für SSL
- DNS-Einträge müssen global zugänglich sein, damit Let's Encrypt SSL-Zertifikate bereitgestellt werden können.
- Die VM muss ihre eigenen Domainnamen auflösen können (interne DNS-Auflösung).
- Konfigurieren Sie die Nameserver korrekt, um OAuth-Authentifizierungs-Timeouts zu vermeiden.

Siehe [Netzwerkanforderungen](../../3_deployment_guide/7_network_requirements/) für detaillierte DNS-Konfiguration und Fehlerbehebung.
:::

---

## Voraussetzungen für lokale Deployments

::: danger Nur für lokales Deployment
**Überspringen Sie diesen gesamten Abschnitt, wenn Sie in Produktion deployen.** Diese Schritte sind nur erforderlich, wenn Sie die
Plattform auf Ihrer lokalen Maschine deployen.
:::

### mkcert installieren

Für das lokale Deployment mit HTTPS-Unterstützung müssen Sie **mkcert** installieren, um selbstsignierte SSL-Zertifikate zu
generieren, die von Ihrem Browser als vertrauenswürdig eingestuft werden.

::: warning
Verwenden Sie selbstsignierte SSL-Zertifikate nur für die lokale Entwicklung. Verwenden Sie sie niemals in Produktions-
oder öffentlichen Umgebungen.
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

**Installation überprüfen:**

```bash
mkcert -version
```

::: tip Was ist mkcert?
**mkcert** ist ein Tool, das lokal vertrauenswürdige SSL-Zertifikate ohne komplexe Konfiguration generiert. Es
installiert automatisch eine lokale Zertifizierungsstelle (CA) in Ihrem System-Vertrauensspeicher, sodass die von ihm
generierten Zertifikate von Ihrem Browser als vertrauenswürdig eingestuft werden.
:::

---

## Nächste Schritte

Fahren Sie mit dem [One-Command Deployment](../2_one_command_deployment/) fort, um die Plattform mithilfe der
erfassten Konfigurationswerte zu deployen.
