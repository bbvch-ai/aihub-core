---
title: Netzwerkanforderungen
source_sha: 559c9f1e16aab50816555b929ccf50fc6804485d8218fa120e340b7df18c7646
---

# Netzwerkanforderungen

Diese Seite behandelt Netzwerkkonnektivität, Firewall-Regeln und Sicherheitsanforderungen für Produktions-Deployments.

## Konnektivität zu externen Services

Die AI-Hub-VM verbindet sich je nach Konfiguration mit externen Services. Alle externen Verbindungen verwenden HTTPS
(Port 443).

Welche Provider Sie benötigen, hängt von Ihrer Deployment-Konfiguration ab.

::: details AI-Service-Endpunkte
| Service       | Endpunkt                            | Port | Zweck                                    |
| ------------- | ----------------------------------- | ---- | ---------------------------------------- |
| Azure OpenAI  | `*.openai.azure.com`                | 443  | LLM-Inferenz, Embeddings, Vision, Audio  |
| Google Gemini | `generativelanguage.googleapis.com` | 443  | LLM-Inferenz                             |
| Jina AI       | `api.jina.ai`                       | 443  | Websuche und Embeddings                  |
| Hugging Face  | `huggingface.co`                    | 443  | Modelldownloads für Self-Hosted-Inferenz |
:::

Agents und Pipelines können Ihre bestehenden Unternehmenssysteme aufrufen.

::: details Beispiel-Endpunkte für Kundenintegrationen
| Service          | Endpunkt                  | Port | Protokoll | Authentifizierung                     |
| ---------------- | ------------------------- | ---- | --------- | ------------------------------------- |
| SharePoint       | `<tenant>.sharepoint.com` | 443  | Graph API | OAuth2 (Azure AD App)                 |
| Confluence       | `<company>.atlassian.net` | 443  | REST      | API-Token                             |
| Custom REST APIs | Kundenspezifisch          | 443  | REST      | Verschiedenes (API-Key, OAuth2, mTLS) |
| SOAP Services    | Kundenspezifisch          | 443  | SOAP      | WS-Security, Basic Auth               |
:::

### Microsoft-Services

Die Benutzerauthentifizierung und -verwaltung verwenden Microsoft Entra ID.

| Service            | Endpunkt                    | Zweck                                     |
| ------------------ | --------------------------- | ----------------------------------------- |
| Microsoft Entra ID | `login.microsoftonline.com` | OAuth2-Benutzerauthentifizierung          |
| Microsoft Graph    | `graph.microsoft.com`       | Benutzerprofile und Gruppenmitgliedschaft |

### Eingehende Verbindungen

Benutzer und Administratoren verbinden sich über diese Ports mit dem AI-Hub.

| Quelle           | Ziel         | Port | Zweck                      |
| ---------------- | ------------ | ---- | -------------------------- |
| Benutzer-Browser | VM Public IP | 443  | Web-UI und Chat-Oberfläche |
| Administratoren  | VM Public IP | 22   | SSH-Administrationszugriff |

## Firewall-Konfiguration

Produktions-Deployments stellen drei eingehende Ports zur Verfügung. Dies minimiert die Angriffsfläche.

### Eingehende Regeln

Konfigurieren Sie diese Regeln in Ihrer Netzwerksicherheitsgruppe (NSG) oder Firewall:

| Priorität | Name           | Port | Protokoll | Zweck                                                              |
| --------- | -------------- | ---- | --------- | ------------------------------------------------------------------ |
| 100       | AllowHTTPS     | 443  | TCP       | Primärer Zugriff auf AI-Hub-Services                               |
| 110       | AllowHTTP      | 80   | TCP       | ACME/Let's Encrypt-Validierung + HTTP→HTTPS-Umleitung              |
| 120       | AllowSSH       | 22   | TCP       | Administrationszugriff (Quell-IPs einschränken)                    |
| 65000     | DenyAllInbound | \*   | \*        | Standardmäßige Ablehnung des gesamten anderen eingehenden Traffics |

::: tip
Beschränken Sie den SSH-Zugriff (Port 22) auf bestimmte Administrator-IP-Adressen oder VPN-Bereiche, anstatt ihn von
jeder Quelle zuzulassen.
:::

### Ausgehende Regeln

Der AI-Hub benötigt ausgehende Konnektivität für externe Integrationen und Updates:

| Priorität | Name       | Port | Protokoll | Zweck                                         |
| --------- | ---------- | ---- | --------- | --------------------------------------------- |
| 100       | AllowHTTPS | 443  | TCP       | API-Aufrufe an LLM-Provider, externe Services |
| 110       | AllowHTTP  | 80   | TCP       | Let's Encrypt-Zertifikatsvalidierung          |
| 120       | AllowDNS   | 53   | UDP       | DNS-Auflösung                                 |

Die Plattform erreicht verschiedene externe APIs basierend auf Ihren Integrationen. Es sind keine zusätzlichen
ausgehenden Beschränkungen erforderlich.

## Verwandte Dokumentation

- [Deployment-Optionen](../1_deployment_options/) - Architektur und Hosting-Strategien
- [Netzwerksicherheit](../../20_security/4_network_security/) - Sicherheitsarchitektur und Defense-in-Depth
- [Authentifizierung](../../20_security/1_authentication/) - Details zur Identity-Provider-Integration
- [Infrastrukturschichten](../../2_architecture/2_infrastructure_layers/) - Überblick über Infrastrukturkomponenten
