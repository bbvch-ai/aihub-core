---
title: Netzwerkanforderungen
source_sha: 390fa9f3616e086bb908851f58b97c27b560ff128e1f01643551419e07077b46
---

# Netzwerkanforderungen

Diese Seite behandelt Netzwerkkonnektivität, Firewall-Regeln und Sicherheitsanforderungen für Produktions-Deployments.

## Konnektivität zu externen Diensten

Die AI-Hub VM verbindet sich je nach Konfiguration mit externen Diensten. Alle externen Verbindungen verwenden HTTPS
(Port 443).

Welche Anbieter Sie benötigen, hängt von Ihrer Deployment-Konfiguration ab.

::: details Endpunkte für KI-Dienste
| Dienst        | Endpunkt                            | Port | Zweck                                         |
| ------------- | ----------------------------------- | ---- | --------------------------------------------- |
| Azure OpenAI  | `*.openai.azure.com`                | 443  | LLM-Inferenz, Embeddings, Vision, Audio       |
| Google Gemini | `generativelanguage.googleapis.com` | 443  | LLM-Inferenz                                  |
| Jina AI       | `api.jina.ai`                       | 443  | Websuche und Embeddings                       |
| Hugging Face  | `huggingface.co`                    | 443  | Modell-Downloads für selbstgehostete Inferenz |
:::

Agenten und Pipelines können Ihre bestehenden Unternehmenssysteme aufrufen.

::: details Beispiel-Endpunkte für Kundenintegrationen
| Dienst           | Endpunkt                  | Port | Protokoll | Authentifizierung                          |
| ---------------- | ------------------------- | ---- | --------- | ------------------------------------------ |
| SharePoint       | `<tenant>.sharepoint.com` | 443  | Graph API | OAuth2 (Azure AD App)                      |
| Confluence       | `<company>.atlassian.net` | 443  | REST      | API-Token                                  |
| Custom REST APIs | Kundenspezifisch          | 443  | REST      | Verschiedene (API-Schlüssel, OAuth2, mTLS) |
| SOAP Services    | Kundenspezifisch          | 443  | SOAP      | WS-Security, Basic Auth                    |
:::

### Microsoft-Dienste

Die Benutzerauthentifizierung und -verwaltung nutzt Microsoft Entra ID.

| Dienst             | Endpunkt                    | Zweck                                     |
| ------------------ | --------------------------- | ----------------------------------------- |
| Microsoft Entra ID | `login.microsoftonline.com` | OAuth2-Benutzerauthentifizierung          |
| Microsoft Graph    | `graph.microsoft.com`       | Benutzerprofile und Gruppenmitgliedschaft |

### Eingehende Verbindungen

Benutzer und Administratoren verbinden sich über diese Ports mit dem AI-Hub.

| Quelle           | Ziel         | Port | Zweck                       |
| ---------------- | ------------ | ---- | --------------------------- |
| Benutzer-Browser | VM Public IP | 443  | Web-UI und Chat-Oberfläche  |
| Administratoren  | VM Public IP | 22   | Administrativer SSH-Zugriff |

## Firewall-Konfiguration

Produktions-Deployments legen drei eingehende Ports offen. Dies minimiert die Angriffsfläche.

### Eingehende Regeln

Konfigurieren Sie diese Regeln in Ihrer Netzwerksicherheitsgruppe (NSG) oder Firewall:

| Priorität | Name           | Port | Protokoll | Zweck                                                            |
| --------- | -------------- | ---- | --------- | ---------------------------------------------------------------- |
| 100       | AllowHTTPS     | 443  | TCP       | Primärer Zugriff auf AI-Hub-Dienste                              |
| 110       | AllowHTTP      | 80   | TCP       | ACME/Let's Encrypt-Validierung + HTTP→HTTPS-Umleitung            |
| 120       | AllowSSH       | 22   | TCP       | Administrativer Zugriff (Quell-IPs einschränken)                 |
| 65000     | DenyAllInbound | \*   | \*        | Standardmäßige Ablehnung allen anderen eingehenden Datenverkehrs |

::: tip
Beschränken Sie den SSH-Zugriff (Port 22) auf bestimmte Administrator-IP-Adressen oder VPN-Bereiche, anstatt ihn von
jeder Quelle zuzulassen.
:::

### Ausgehende Regeln

Der AI-Hub benötigt ausgehende Konnektivität für externe Integrationen und Updates:

| Priorität | Name       | Port | Protokoll | Zweck                                        |
| --------- | ---------- | ---- | --------- | -------------------------------------------- |
| 100       | AllowHTTPS | 443  | TCP       | API-Aufrufe an LLM-Anbieter, externe Dienste |
| 110       | AllowHTTP  | 80   | TCP       | Let's Encrypt-Zertifikatsvalidierung         |
| 120       | AllowDNS   | 53   | UDP       | DNS-Auflösung                                |

Die Plattform erreicht verschiedene externe APIs basierend auf Ihren Integrationen. Es sind keine zusätzlichen
ausgehenden Einschränkungen erforderlich.

## Zugehörige Dokumentation

- [Deployment-Optionen](../1_deployment_options/) – Architektur und Hosting-Strategien
- [Netzwerksicherheit](../../19_security/4_network_security/) – Sicherheitsarchitektur und Defense-in-Depth
- [Authentifizierung](../../19_security/1_authentication/) – Details zur Identity Provider-Integration
- [Infrastruktur-Ebenen](../../2_architecture/2_infrastructure_layers/) – Überblick über Infrastrukturkomponenten
