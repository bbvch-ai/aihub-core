---
title: Netzwerkanforderungen
source_sha: 9edb2d8fce65331a2f6be7343396d9aae1287b2e9424a253de97ab502829535b
---

# Netzwerkanforderungen

Diese Seite behandelt Netzwerkkonnektivität, Firewall-Regeln und Sicherheitsanforderungen für Produktions-Deployments.

## Konnektivität zu externen Services

Die AI-Hub VM stellt Verbindungen zu externen Services her, abhängig von Ihrer Konfiguration. Alle externen Verbindungen
nutzen HTTPS (Port 443).

Welche Anbieter Sie benötigen, hängt von Ihrer Deployment-Konfiguration ab.

::: details AI-Service-Endpunkte
| Service       | Endpunkt                            | Port | Zweck                                         |
| ------------- | ----------------------------------- | ---- | --------------------------------------------- |
| Azure OpenAI  | `*.openai.azure.com`                | 443  | LLM-Inferenz, Embeddings, Vision, Audio       |
| Google Gemini | `generativelanguage.googleapis.com` | 443  | LLM-Inferenz                                  |
| Jina AI       | `api.jina.ai`                       | 443  | Websuche und Embeddings                       |
| Hugging Face  | `huggingface.co`                    | 443  | Modell-Downloads für selbstgehostete Inferenz |
:::

Agents und Pipelines können Ihre bestehenden Unternehmenssysteme aufrufen.

::: details Beispiel für Endpunkte zur Kundenintegration
| Service          | Endpunkt                  | Port | Protokoll | Authentifizierung                     |
| ---------------- | ------------------------- | ---- | --------- | ------------------------------------- |
| SharePoint       | `<tenant>.sharepoint.com` | 443  | Graph API | OAuth2 (Azure AD App)                 |
| Confluence       | `<company>.atlassian.net` | 443  | REST      | API Token                             |
| Custom REST APIs | Kundenspezifisch          | 443  | REST      | Verschiedenes (API Key, OAuth2, mTLS) |
| SOAP Services    | Kundenspezifisch          | 443  | SOAP      | WS-Security, Basic Auth               |
:::

### Identity Provider-Services

Für die Benutzerauthentifizierung ist eine Konnektivität zu Ihrem konfigurierten OIDC-Anbieter erforderlich. Das
folgende Beispiel zeigt Microsoft Entra ID Endpunkte; ersetzen Sie diese bei Bedarf durch die Endpunkte Ihres Anbieters.

| Service            | Endpunkt                    | Zweck                                                                                   |
| ------------------ | --------------------------- | --------------------------------------------------------------------------------------- |
| Microsoft Entra ID | `login.microsoftonline.com` | OAuth2/OIDC-Benutzerauthentifizierung                                                   |
| Microsoft Graph    | `graph.microsoft.com`       | Nur für SharePoint/OneDrive Pipeline-Quellen erforderlich (nicht für Authentifizierung) |

### Eingehende Verbindungen

Benutzer und Administratoren verbinden sich über diese Ports mit dem AI-Hub.

| Quelle           | Ziel                  | Port | Zweck                      |
| ---------------- | --------------------- | ---- | -------------------------- |
| Benutzer-Browser | Öffentliche IP der VM | 443  | Web-UI und Chat-Oberfläche |
| Administratoren  | Öffentliche IP der VM | 22   | Administrativer SSH-Zugang |

## Firewall-Konfiguration

Produktions-Deployments legen drei eingehende Ports frei. Dies minimiert die Angriffsfläche.

### Eingehende Regeln

Konfigurieren Sie diese Regeln in Ihrer Netzwerksicherheitsgruppe (NSG) oder Firewall:

| Priorität | Name           | Port | Protokoll | Zweck                                                           |
| --------- | -------------- | ---- | --------- | --------------------------------------------------------------- |
| 100       | AllowHTTPS     | 443  | TCP       | Primärer Zugang zu AI-Hub Services                              |
| 110       | AllowHTTP      | 80   | TCP       | ACME/Let's Encrypt Validierung + HTTP→HTTPS-Weiterleitung       |
| 120       | AllowSSH       | 22   | TCP       | Administrativer Zugang (Quell-IPs einschränken)                 |
| 65000     | DenyAllInbound | \*   | \*        | Standardmäßige Ablehnung aller anderen eingehenden Verbindungen |

::: tip
Beschränken Sie den SSH-Zugang (Port 22) auf bestimmte Administrator-IP-Adressen oder VPN-Bereiche, anstatt ihn von
jeder Quelle aus zu erlauben.
:::

### Ausgehende Regeln

Der AI-Hub benötigt ausgehende Konnektivität für externe Integrationen und Updates:

| Priorität | Name       | Port | Protokoll | Zweck                                         |
| --------- | ---------- | ---- | --------- | --------------------------------------------- |
| 100       | AllowHTTPS | 443  | TCP       | API-Aufrufe an LLM-Anbieter, externe Services |
| 110       | AllowHTTP  | 80   | TCP       | Let's Encrypt Zertifikatsvalidierung          |
| 120       | AllowDNS   | 53   | UDP       | DNS-Auflösung                                 |

Die Plattform erreicht verschiedene externe APIs basierend auf Ihren Integrationen. Es sind keine zusätzlichen
ausgehenden Beschränkungen erforderlich.

## Verwandte Dokumentation

- [Deployment-Optionen](../1_deployment_options/) - Architektur- und Hosting-Strategien
- [Netzwerksicherheit](../../20_security/4_network_security/) - Sicherheitsarchitektur und Defense-in-Depth
- [Authentifizierung](../../20_security/1_authentication/) - Details zur Identity Provider-Integration
- [Infrastruktur-Ebenen](../../2_architecture/2_infrastructure_layers/) - Übersicht der Infrastrukturkomponenten
