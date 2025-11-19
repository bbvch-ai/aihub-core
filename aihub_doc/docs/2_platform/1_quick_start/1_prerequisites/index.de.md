---
title: Voraussetzungen
source_sha: 468d25a4e6af4e01b32f598e54e934fa3111dc6430ca835013e7d8b21b026054
---

# Voraussetzungen

Dieser Leitfaden behandelt die Voraussetzungen für die Bereitstellung der AI-Hub Plattform.

::: tip Wählen Sie Ihren Bereitstellungstyp
Die Voraussetzungen unterscheiden sich je nach Bereitstellungstyp:

- **Produktionsbereitstellung**: Bereitstellung auf einem Server mit einem echten Domainnamen und automatischen
  SSL-Zertifikaten
- **Lokale Bereitstellung**: Ausführung auf Ihrem lokalen Computer mit `127.0.0.1.nip.io` und selbstsignierten
  Zertifikaten

Befolgen Sie nur die Abschnitte, die für Ihren Bereitstellungstyp relevant sind.
:::

## Allgemeine Anforderungen (alle Bereitstellungen)

Diese Anforderungen gelten sowohl für Produktions- als auch für lokale Bereitstellungen.

### Systemanforderungen

#### Minimale Spezifikationen

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
Die Plattform führt mehrere Dienste gleichzeitig aus (Datenbanken, Vektorspeicher, LLM-Proxies, Weboberflächen,
Verarbeitungs-Engines). Systeme unterhalb der Mindestspezifikationen werden Dienstfehler oder eine verminderte Leistung
aufweisen.
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

- **Geöffnete Ports**: 80 (HTTP), 443 (HTTPS)
- **Internetzugang**: Erforderlich für Docker-Image-Downloads und Updates

#### Überprüfung

Testen Sie Ihre Docker-Installation:

```bash
docker --version
docker compose --version
docker run hello-world
```

Alle Befehle müssen erfolgreich abgeschlossen werden.

### Einrichtung des Authentifizierungsanbieters

Die Plattform erfordert einen OAuth2/OpenID Connect-Identitätsanbieter für sowohl Produktions- als auch lokale
Bereitstellungen. Dieser Leitfaden dokumentiert die Einrichtung von Azure Entra ID. Andere Anbieter (Google, Okta,
Auth0) können nach ähnlichen Mustern konfiguriert werden.

#### Einrichtung von Azure Entra ID

Führen Sie die folgenden Schritte im Azure-Portal aus, um die Authentifizierung vorzubereiten:

**Schritt 1: App-Registrierung erstellen**

1. Navigieren Sie zu **Azure-Portal** → **Azure Active Directory** → **App-Registrierungen**
2. Klicken Sie auf **„Neue Registrierung“**
3. Konfigurieren Sie die Registrierung:
   - **Name**: `Swiss AI Hub` (oder die Namenskonvention Ihrer Organisation)
   - **Unterstützte Kontotypen**: Wählen Sie basierend auf den Anforderungen
     - `Konten nur in diesem Organisationsverzeichnis` (einzelner Mandant – für die meisten Bereitstellungen empfohlen)
   - **Umleitungs-URI**: Leer lassen (wird in Schritt 5 konfiguriert)
4. Klicken Sie auf **„Registrieren“**

**Schritt 2: Token-Version konfigurieren**

Die Plattform erfordert Zugriffstoken-Version 2 für die ordnungsgemäße Authentifizierung.

1. Navigieren Sie zu **„Manifest“**
2. Suchen Sie die Eigenschaft `requestedAccessTokenVersion`
3. Ändern Sie den Wert von `null` oder `1` auf `2`:
   ```json
   "requestedAccessTokenVersion": 2
   ```
4. Klicken Sie oben im Manifest-Editor auf **„Speichern“**

::: warning
Zugriffstoken-Version 2 ist erforderlich, damit die Plattform korrekt funktioniert. Token der Version 1 werden nicht
unterstützt und führen zu Authentifizierungsfehlern.
:::

**Schritt 3: API-Berechtigungen konfigurieren**

1. Navigieren Sie zu **„API-Berechtigungen“** → **„Berechtigung hinzufügen“**
2. Wählen Sie **„Microsoft Graph“** → **„Delegierte Berechtigungen“**
3. Fügen Sie die folgenden Berechtigungen hinzu:
   - `openid` - Erforderlich für OpenID Connect-Authentifizierung
   - `profile` - Erforderlich für grundlegende Benutzerprofilinformationen
   - `email` - Erforderlich für die E-Mail-Adresse
   - `offline_access` - Erforderlich für Aktualisierungstoken (Refresh Tokens)
   - `User.Read` - Erforderlich zum Lesen des Benutzerprofils
   - `Group.Read.All` - Erforderlich für Gruppenmitgliedschaftsinformationen
4. Wählen Sie **„Microsoft Graph“** → **„Anwendungsberechtigungen“**
5. Fügen Sie die folgenden Berechtigungen hinzu:
   - `User.ReadBasic.All` - Erforderlich zum Lesen grundlegender Profile aller Benutzer
   - `Directory.Read.All` - Erforderlich zum Lesen von Verzeichnisdaten
   - `ProfilePhoto.Read.All` - Erforderlich zum Lesen von Profilfotos
6. Klicken Sie auf **„Administratoreinwilligung für [Ihre Organisation] erteilen“**
7. Überprüfen Sie, ob alle Berechtigungen den Status **„Gewährt für [Ihre Organisation]“** anzeigen

::: warning
Alle aufgeführten Berechtigungen sind für die Funktionalität der Plattform erforderlich. Fehlende Berechtigungen führen
während der Bereitstellung zu Authentifizierungs- oder Autorisierungsfehlern.
:::

**Schritt 4: Client-Geheimnis erstellen**

1. Navigieren Sie zu **„Zertifikate & Geheimnisse“** → **„Clientgeheimnisse“** → **„Neues Clientgeheimnis“**
2. Konfigurieren Sie das Geheimnis:
   - **Beschreibung**: Geben Sie einen aussagekräftigen Namen ein (z. B. `AI-Hub Secret`)
   - **Läuft ab**: Wählen Sie den Ablaufzeitraum (12–24 Monate empfohlen)
3. Klicken Sie auf **„Hinzufügen“**
4. **Kopieren Sie sofort den geheimen Wert** an einen sicheren Speicherort
5. Notieren Sie diesen Wert als `[CLIENT_SECRET]` für die Bereitstellungskonfiguration

::: danger
Der Wert des Client-Geheimnisses wird nur einmal unmittelbar nach der Erstellung angezeigt. Geht der Wert verloren, muss
ein neues Geheimnis erstellt werden. Speichern Sie ihn in einem Passwort-Manager oder einem sicheren Tresor.
:::

**Schritt 5: App-Rollen konfigurieren**

App-Rollen ermöglichen die rollenbasierte Zugriffssteuerung (RBAC) für Plattformbenutzer.

Erstellen Sie drei App-Rollen nach diesem Prozess:

1. Navigieren Sie zu **„App-Rollen“** → **„App-Rolle erstellen“**
2. Erstellen Sie jede der folgenden Rollen:

**Administrator-Rolle:**

- **Anzeigename**: `AIHubAdmin`
- **Zulässige Mitgliedstypen**: `Benutzer/Gruppen`
- **Wert**: `AIHubAdmin`
- **Beschreibung**: `Administratorzugriff auf die AI-Hub Plattform`

**Benutzer-Rolle:**

- **Anzeigename**: `AIHubUser`
- **Zulässige Mitgliedstypen**: `Benutzer/Gruppen`
- **Wert**: `AIHubUser`
- **Beschreibung**: `Standard-Benutzerzugriff auf die AI-Hub Plattform`

**Entwickler-Rolle:**

- **Anzeigename**: `AIHubDeveloper`
- **Zulässige Mitgliedstypen**: `Benutzer/Gruppen`
- **Wert**: `AIHubDeveloper`
- **Beschreibung**: `Entwicklerzugriff auf AI-Hub Plattformdienste (Dagster, Data Lake)`

::: tip
Die Rolle `AIHubDeveloper` ist erforderlich, um auf das Dagster Pipeline-Orchestrierungs-Dashboard und die SeaweedFS
Data Lake-Konsole zuzugreifen. Benutzer ohne diese Rolle können weiterhin die Haupt-AI-Hub-Oberfläche und OpenWebUI
nutzen.
:::

**Schritt 6: SPA-Umleitungs-URIs konfigurieren**

Single-Page Application (SPA)-Umleitungs-URIs sind für die Hauptweb-Oberfläche mit mehrsprachiger Unterstützung
erforderlich.

1. Navigieren Sie zu **„Authentifizierung“** → **„Plattform hinzufügen“** → **„Single-page-Anwendung“**

2. Fügen Sie Umleitungs-URIs basierend auf Ihrem Bereitstellungstyp hinzu:

   **Für die Produktion:** Ersetzen Sie `your-domain.com` durch Ihre tatsächliche Domain

   ```
   https://your-domain.com/de/auth/callback
   https://your-domain.com/en/auth/callback
   https://your-domain.com/it/auth/callback
   https://your-domain.com/fr/auth/callback
   ```

   **Für die lokale Bereitstellung:** Verwenden Sie `127.0.0.1.nip.io`

   ```
   https://127.0.0.1.nip.io/de/auth/callback
   https://127.0.0.1.nip.io/en/auth/callback
   https://127.0.0.1.nip.io/it/auth/callback
   https://127.0.0.1.nip.io/fr/auth/callback
   ```

   ::: tip
Sie können sowohl Produktions- als auch lokale URIs zur gleichen App-Registrierung zu Testzwecken hinzufügen.
   :::

3. Konfigurieren Sie die Token-Einstellungen:
   - **Zugriffstoken** aktivieren (für implizite Flows verwendet)
   - **ID-Token** aktivieren (für implizite Flows verwendet)
4. Klicken Sie auf **„Konfigurieren“**

**Schritt 7: Webanwendungs-Umleitungs-URIs konfigurieren**

Webanwendungs-Umleitungs-URIs sind für integrierte Dienste (OpenWebUI, Dagster, Data Lake) erforderlich.

1. Navigieren Sie zu **„Authentifizierung“** → **„Plattform hinzufügen“** → **„Web“**

2. Fügen Sie Umleitungs-URIs basierend auf Ihrem Bereitstellungstyp hinzu:

   **Für die Produktion:** Ersetzen Sie `your-domain.com` durch Ihre tatsächliche Domain

   ```
   https://openwebui.your-domain.com/oauth/oidc/callback
   https://dagster.your-domain.com/oauth2/callback
   https://datalake.your-domain.com/oauth2/callback
   ```

   **Für die lokale Bereitstellung:** Verwenden Sie `127.0.0.1.nip.io`

   ```
   https://openwebui.127.0.0.1.nip.io/oauth/oidc/callback
   https://dagster.127.0.0.1.nip.io/oauth2/callback
   https://datalake.127.0.0.1.nip.io/oauth2/callback
   ```

3. Konfigurieren Sie die Token-Einstellungen:

   - **ID-Token** aktivieren (für hybride Flows verwendet)

4. Klicken Sie auf **„Konfigurieren“**

::: warning Unterscheidung des Plattformtyps
Die Konfiguration des Plattformtyps (SPA vs. Web) ist entscheidend für die Auswahl des OAuth2-Flows:

- **SPA-Plattform**: Sprachspezifische Callbacks (`/de/`, `/en/`, `/fr/`, `/it/`) verwenden den PKCE-Flow ohne
  Client-Geheimnis.
- **Web-Plattform**: Service-Callbacks (`openwebui`, `dagster`, `datalake`) verwenden den Autorisierungscode-Flow mit
  Client-Geheimnis.

Falsch konfigurierte Plattformtypen führen zum Authentifizierungsfehler
`AADSTS9002326: Cross-origin token redemption is permitted only for the 'Single-Page Application' client-type`. Stellen
Sie sicher, dass die Umleitungs-URIs unter dem korrekten Plattformtyp registriert sind.
:::

**Erforderliche Authentifizierungsinformationen**

Nach Abschluss der Azure-Einrichtung sollten Sie über Folgendes verfügen:

- `[CLIENT_ID]` – Anwendungs- (Client-) ID
- `[CLIENT_SECRET]` – Client-Geheimniswert
- `[TENANT_ID]` – Verzeichnis- (Mandanten-) ID

Diese Werte benötigen Sie während der Konfiguration der Plattformbereitstellung.

---

## Voraussetzungen für die Produktionsbereitstellung

::: danger Nur für Produktionsbereitstellungen
**Überspringen Sie diesen gesamten Abschnitt, wenn Sie lokal testen.** Diese Schritte sind nur erforderlich, wenn Sie
auf einem Server mit einem echten Domainnamen bereitstellen.
:::

### DNS-Konfiguration

Konfigurieren Sie DNS-Einträge für Ihre Domain. Die Plattform erfordert **sieben Subdomains**, die auf die öffentliche
IP-Adresse Ihres Servers verweisen:

- `aihub.example.com` – Haupt-Weboberfläche
- `openwebui.aihub.example.com` – Chat-UI
- `dagster.aihub.example.com` – Pipeline-Orchestrierung
- `datalake.aihub.example.com` – Data Lake-Konsole
- `datalake-api.aihub.example.com` – S3-API
- `attu.aihub.example.com` – Milvus Vektordatenbank-UI
- `traefik.aihub.example.com` – Reverse Proxy Dashboard

Ersetzen Sie `aihub.example.com` durch Ihre tatsächliche Domain. Erstellen Sie A-Records oder CNAMEs für alle sieben
Subdomains, die auf die IP-Adresse Ihres Servers verweisen.

::: warning DNS-Anforderungen für SSL
- DNS-Einträge müssen für die Bereitstellung von Let's Encrypt SSL-Zertifikaten global zugänglich sein.
- Die VM muss in der Lage sein, ihre eigenen Domainnamen aufzulösen (interne DNS-Auflösung).
- Konfigurieren Sie die Nameserver korrekt, um OAuth-Authentifizierungs-Timeouts zu vermeiden.

Siehe [Netzwerkanforderungen](/de/docs/2_platform/3_deployment_guide/7_network_requirements/) für detaillierte
DNS-Konfiguration und Fehlerbehebung.
:::

---

## Voraussetzungen für die lokale Bereitstellung

::: danger Nur für die lokale Bereitstellung
**Überspringen Sie diesen gesamten Abschnitt, wenn Sie in Produktion bereitstellen.** Diese Schritte sind nur
erforderlich, wenn Sie die Plattform auf Ihrem lokalen Rechner bereitstellen.
:::

### mkcert installieren

Für die lokale Bereitstellung mit HTTPS-Unterstützung müssen Sie **mkcert** installieren, um selbstsignierte
SSL-Zertifikate zu generieren, die von Ihrem Browser als vertrauenswürdig eingestuft werden.

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

**Installation überprüfen:**

```bash
mkcert -version
```

::: tip Was ist mkcert?
**mkcert** ist ein Tool, das lokal vertrauenswürdige SSL-Zertifikate ohne komplexe Konfiguration generiert. Es
installiert automatisch eine lokale Zertifizierungsstelle (CA) in Ihrem System-Vertrauensspeicher, sodass die
generierten Zertifikate von Ihrem Browser als vertrauenswürdig eingestuft werden.
:::

---

## Nächste Schritte

Fahren Sie mit der [Ein-Befehl-Bereitstellung](/de/docs/2_platform/1_quick_start/2_one_command_deployment/) fort, um die
Plattform mit den aufgezeichneten Konfigurationswerten bereitzustellen.
