---
title: Netzwerkanforderungen
source_sha: e0c27a73a2b2c531b880a5d4700fbe242b192bb5845920f2744dc3a0c3cdfbf2
---

# Netzwerkanforderungen

Diese Seite behandelt Netzwerkkonnektivität, Firewall-Regeln und Sicherheitsanforderungen für Produktions-Deployments.

## Externe Service-Konnektivität

Die AI-Hub VM stellt Verbindungen zu externen Services her, abhängig von Ihrer Konfiguration. Alle externen Verbindungen
verwenden HTTPS (Port 443).

Welche Anbieter Sie benötigen, hängt von Ihrer Deployment-Konfiguration ab.

::: details AI-Dienstendpunkte
| Dienst        | Endpunkt                            | Port | Zweck                                         |
| ------------- | ----------------------------------- | ---- | --------------------------------------------- |
| Azure OpenAI  | `*.openai.azure.com`                | 443  | LLM inference, embeddings, vision, audio      |
| Google Gemini | `generativelanguage.googleapis.com` | 443  | LLM inference                                 |
| Jina AI       | `api.jina.ai`                       | 443  | Websuche und Embeddings                       |
| Hugging Face  | `huggingface.co`                    | 443  | Modell-Downloads für selbstgehostete Inferenz |
:::

Agenten und Pipelines können Ihre bestehenden Unternehmenssysteme aufrufen.

::: details Beispiel-Endpunkte für Kundenintegrationen
| Dienst           | Endpunkt                  | Port | Protokoll | Authentifizierung                    |
| ---------------- | ------------------------- | ---- | --------- | ------------------------------------ |
| SharePoint       | `<tenant>.sharepoint.com` | 443  | Graph API | OAuth2 (Azure AD App)                |
| Confluence       | `<company>.atlassian.net` | 443  | REST      | API Token                            |
| Custom REST APIs | Kundenspezifisch          | 443  | REST      | Verschiedene (API Key, OAuth2, mTLS) |
| SOAP Services    | Kundenspezifisch          | 443  | SOAP      | WS-Security, Basic Auth              |
:::

### Microsoft-Dienste

Die Benutzerauthentifizierung und -verwaltung verwendet Microsoft Entra ID.

| Dienst             | Endpunkt                    | Zweck                                     |
| ------------------ | --------------------------- | ----------------------------------------- |
| Microsoft Entra ID | `login.microsoftonline.com` | OAuth2-Benutzerauthentifizierung          |
| Microsoft Graph    | `graph.microsoft.com`       | Benutzerprofile und Gruppenmitgliedschaft |

### Eingehende Verbindungen

Benutzer und Administratoren verbinden sich über diese Ports mit dem AI-Hub.

| Quelle           | Ziel              | Port | Zweck                       |
| ---------------- | ----------------- | ---- | --------------------------- |
| Benutzer-Browser | Öffentliche VM-IP | 443  | Web-UI und Chat-Oberfläche  |
| Administratoren  | Öffentliche VM-IP | 22   | Administrativer SSH-Zugriff |

## Firewall-Konfiguration

Produktions-Deployments stellen drei eingehende Ports bereit. Dies minimiert die Angriffsfläche.

### Eingehende Regeln

Konfigurieren Sie diese Regeln in Ihrer Netzwerksicherheitsgruppe (NSG) oder Firewall:

| Priorität | Name           | Port | Protokoll | Zweck                                                           |
| --------- | -------------- | ---- | --------- | --------------------------------------------------------------- |
| 100       | AllowHTTPS     | 443  | TCP       | Primärer Zugriff auf AI-Hub-Dienste                             |
| 110       | AllowHTTP      | 80   | TCP       | ACME/Let's Encrypt Validierung + HTTP→HTTPS Weiterleitung       |
| 120       | AllowSSH       | 22   | TCP       | Administrativer Zugriff (Quell-IPs einschränken)                |
| 65000     | DenyAllInbound | \*   | \*        | Standardmäßige Ablehnung aller anderen eingehenden Verbindungen |

::: tip
Beschränken Sie den SSH-Zugriff (Port 22) auf bestimmte Administrator-IP-Adressen oder VPN-Bereiche, anstatt ihn von
jeder Quelle zuzulassen.
:::

### Ausgehende Regeln

Der AI-Hub benötigt ausgehende Konnektivität für externe Integrationen und Updates:

| Priorität | Name       | Port | Protokoll | Zweck                                        |
| --------- | ---------- | ---- | --------- | -------------------------------------------- |
| 100       | AllowHTTPS | 443  | TCP       | API-Aufrufe an LLM-Anbieter, externe Dienste |
| 110       | AllowHTTP  | 80   | TCP       | Let's Encrypt Zertifikatvalidierung          |
| 120       | AllowDNS   | 53   | UDP       | DNS-Auflösung                                |

Die Plattform greift basierend auf Ihren Integrationen auf verschiedene externe APIs zu. Es sind keine zusätzlichen
ausgehenden Beschränkungen erforderlich.

## Zugehörige Dokumentation

- [Deployment-Optionen](../1_deployment_options/) - Architektur- und Hosting-Strategien
- [Netzwerksicherheit](../../19_security/4_network_security/) - Sicherheitsarchitektur und Defense-in-Depth
- [Authentifizierung](../../19_security/1_authentication/) - Details zur Identity-Provider-Integration
- [Infrastruktur-Ebenen](../../2_architecture/2_infrastructure_layers/) - Übersicht der Infrastrukturkomponenten
