---
title: Netzwerkanforderungen
source_sha: ff6a8b736a64b60018b8bc29a7e98c8074dd321dee568ff32fc0cfef304ea4e0
---

# Netzwerkanforderungen

Diese Seite behandelt Netzwerkkonnektivität, Firewall-Regeln und Sicherheitsanforderungen für Produktions-Deployments.

## Konnektivität zu externen Services

Die AI-Hub VM stellt Verbindungen zu externen Services her, abhängig von Ihrer Konfiguration. Alle externen Verbindungen
verwenden HTTPS (Port 443).

Welche Anbieter Sie benötigen, hängt von Ihrer Deployment-Konfiguration ab.

::: details KI-Service-Endpunkte
| Service         | Endpunkt                                      | Port | Zweck                                             |
| --------------- | --------------------------------------------- | ---- | ------------------------------------------------- |
| Swiss LLM Cloud | Configured via `SWISS_LLM_CLOUD_API_BASE_URL` | 443  | Texterzeugung, Embedding, Reranking, Whisper, OCR |
| Jina AI         | `api.jina.ai`                                 | 443  | Websuche und Embeddings                           |
| Hugging Face    | `huggingface.co`                              | 443  | Modelldownloads für selbst gehostete Inferenz     |

GPU-Deployments, die lokales vLLM nutzen, benötigen keine ausgehende Konnektivität zu LLM-Anbietern.
:::

Agents und Pipelines können Ihre bestehenden Unternehmenssysteme aufrufen.

::: details Beispiel-Endpunkte für Kundenintegrationen
| Service          | Endpunkt                  | Port | Protokoll | Authentifizierung                    |
| ---------------- | ------------------------- | ---- | --------- | ------------------------------------ |
| SharePoint       | `<tenant>.sharepoint.com` | 443  | Graph API | OAuth2 (Azure AD App)                |
| Confluence       | `<company>.atlassian.net` | 443  | REST      | API Token                            |
| Custom REST APIs | Kundenspezifisch          | 443  | REST      | Verschiedene (API Key, OAuth2, mTLS) |
| SOAP Services    | Kundenspezifisch          | 443  | SOAP      | WS-Security, Basic Auth              |
:::

### Identity Provider Services

Die Benutzerauthentifizierung erfordert Konnektivität zu Ihrem konfigurierten OIDC-Provider. Das folgende Beispiel zeigt
Microsoft Entra ID Endpunkte; ersetzen Sie diese bei Bedarf durch die Endpunkte Ihres Anbieters.

| Service            | Endpunkt                    | Zweck                                                                                   |
| ------------------ | --------------------------- | --------------------------------------------------------------------------------------- |
| Microsoft Entra ID | `login.microsoftonline.com` | OAuth2/OIDC Benutzerauthentifizierung                                                   |
| Microsoft Graph    | `graph.microsoft.com`       | Nur für SharePoint/OneDrive Pipeline-Quellen erforderlich (nicht für Authentifizierung) |

### Eingehende Verbindungen

Benutzer und Administratoren verbinden sich über diese Ports mit dem AI-Hub.

| Quelle           | Ziel              | Port | Zweck                       |
| ---------------- | ----------------- | ---- | --------------------------- |
| Benutzer-Browser | VM öffentliche IP | 443  | Web-UI und Chat-Oberfläche  |
| Administratoren  | VM öffentliche IP | 22   | Administrativer SSH-Zugriff |

## Firewall-Konfiguration

Produktions-Deployments legen drei eingehende Ports offen. Dies minimiert die Angriffsfläche.

### Eingehende Regeln

Konfigurieren Sie diese Regeln in Ihrer Netzwerksicherheitsgruppe (NSG) oder Firewall:

| Priorität | Name           | Port | Protokoll | Zweck                                                               |
| --------- | -------------- | ---- | --------- | ------------------------------------------------------------------- |
| 100       | AllowHTTPS     | 443  | TCP       | Primärer Zugriff auf AI-Hub Services                                |
| 110       | AllowHTTP      | 80   | TCP       | ACME/Let's Encrypt Validierung + HTTP→HTTPS Umleitung               |
| 120       | AllowSSH       | 22   | TCP       | Administrativer Zugriff (Quell-IPs einschränken)                    |
| 65000     | DenyAllInbound | \*   | \*        | Standardmäßige Verweigerung allen anderen eingehenden Datenverkehrs |

::: tip
Beschränken Sie den SSH-Zugriff (Port 22) auf bestimmte Administrator-IP-Adressen oder VPN-Bereiche, anstatt ihn von
jeder Quelle zuzulassen.
:::

### Ausgehende Regeln

Der AI-Hub benötigt ausgehende Konnektivität für externe Integrationen und Updates:

| Priorität | Name       | Port | Protokoll | Zweck                                         |
| --------- | ---------- | ---- | --------- | --------------------------------------------- |
| 100       | AllowHTTPS | 443  | TCP       | API-Aufrufe an LLM-Provider, externe Services |
| 110       | AllowHTTP  | 80   | TCP       | Let's Encrypt Zertifikatsvalidierung          |
| 120       | AllowDNS   | 53   | UDP       | DNS-Auflösung                                 |

Die Plattform erreicht verschiedene externe APIs basierend auf Ihren Integrationen. Es sind keine zusätzlichen
ausgehenden Einschränkungen erforderlich.

## Verwandte Dokumentation

- [Deployment-Optionen](../1_deployment_options/) - Architektur- und Hosting-Strategien
- [Netzwerksicherheit](../../20_security/4_network_security/) - Sicherheitsarchitektur und Defense-in-Depth
- [Authentifizierung](../../20_security/1_authentication/) - Details zur Identity Provider Integration
- [Infrastruktur-Ebenen](../../2_architecture/2_infrastructure_layers/) - Übersicht der Infrastrukturkomponenten
