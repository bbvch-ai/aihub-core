---
title: Netzwerkanforderungen
source_sha: "529dc4256a9445dfde009cc5f633e87a5a4e9111ab33ecb52e44431fad60e702"
---

# Netzwerkanforderungen

Diese Seite behandelt Netzwerkkonnektivität, Firewall-Regeln und Sicherheitsanforderungen für Produktionsumgebungen.

## Konnektivität zu externen Diensten

Die AI-Hub VM stellt Verbindungen zu externen Diensten her, abhängig von Ihrer Konfiguration. Alle externen Verbindungen verwenden HTTPS (Port 443).

Welche Anbieter Sie benötigen, hängt von Ihrer Bereitstellungskonfiguration ab.

::: details AI-Dienst-Endpunkte
| Dienst | Endpunkt | Port | Zweck |
|---------|----------|------|---------|
| Azure OpenAI  | `*.openai.azure.com` | 443 | LLM-Inferenz, Embeddings, Vision, Audio |
| Google Gemini | `generativelanguage.googleapis.com` | 443 | LLM-Inferenz |
| Jina AI | `api.jina.ai` | 443 | Websuche und Embeddings |
| Hugging Face | `huggingface.co` | 443 | Modelldownloads für selbst gehostete Inferenz |
:::

Agenten und Pipelines können Ihre bestehenden Unternehmenssysteme aufrufen.

::: details Beispiel-Endpunkte für Kundenintegrationen
| Dienst | Endpunkt | Port | Protokoll | Authentifizierung |
|---------|----------|------|----------|----------------|
| SharePoint | `<tenant>.sharepoint.com` | 443 | Graph API | OAuth2 (Azure AD App) |
| Confluence | `<company>.atlassian.net` | 443 | REST | API Token |
| Custom REST APIs | Kundenspezifisch | 443 | REST | Verschiedenes (API Key, OAuth2, mTLS) |
| SOAP Services | Kundenspezifisch | 443 | SOAP | WS-Security, Basic Auth |
:::

### Microsoft-Dienste

Die Benutzerauthentifizierung und -verwaltung verwenden Microsoft Entra ID.

| Dienst | Endpunkt | Zweck |
|---------|----------|---------|
| Microsoft Entra ID | `login.microsoftonline.com` | OAuth2 Benutzerauthentifizierung |
| Microsoft Graph | `graph.microsoft.com` | Benutzerprofile und Gruppenmitgliedschaft |

### Eingehende Verbindungen

Benutzer und Administratoren verbinden sich über diese Ports mit dem AI-Hub.

| Quelle | Ziel | Port | Zweck |
|--------|-------------|------|---------|
| Benutzerbrowser | VM Öffentliche IP | 443 | Web-UI und Chat-Interface |
| Administratoren | VM Öffentliche IP | 22 | SSH Administrativer Zugriff |

## Firewall-Konfiguration

Produktionsbereitstellungen exponieren drei eingehende Ports. Dies minimiert die Angriffsfläche.

### Eingehende Regeln

Konfigurieren Sie diese Regeln in Ihrer Netzwerksicherheitsgruppe (NSG) oder Firewall:

| Priorität | Name | Port | Protokoll | Zweck |
|----------|------|------|----------|---------|
| 100 | AllowHTTPS | 443 | TCP | Primärer Zugriff auf AI-Hub-Dienste |
| 110 | AllowHTTP | 80 | TCP | ACME/Let's Encrypt Validierung + HTTP→HTTPS-Umleitung |
| 120 | AllowSSH | 22 | TCP | Administrativer Zugriff (Quell-IPs einschränken) |
| 65000 | DenyAllInbound | \* | \* | Standardmäßige Ablehnung des gesamten anderen eingehenden Datenverkehrs |

::: tip
Beschränken Sie den SSH-Zugriff (Port 22) auf bestimmte Administrator-IP-Adressen oder VPN-Bereiche, anstatt ihn von jeder Quelle zuzulassen.
:::

### Ausgehende Regeln

Der AI-Hub benötigt ausgehende Konnektivität für externe Integrationen und Updates:

| Priorität | Name | Port | Protokoll | Zweck |
|----------|------|------|----------|---------|
| 100 | AllowHTTPS | 443 | TCP | API-Aufrufe an LLM-Anbieter, externe Dienste |
| 110 | AllowHTTP | 80 | TCP | Let's Encrypt Zertifikatsvalidierung |
| 120 | AllowDNS | 53 | UDP | DNS-Auflösung |

Die Plattform erreicht verschiedene externe APIs basierend auf Ihren Integrationen. Es sind keine zusätzlichen ausgehenden Beschränkungen erforderlich.

## Verwandte Dokumentation

- [Bereitstellungsoptionen](../1_deployment_options/) - Architektur und Hosting-Strategien
- [Netzwerksicherheit](../../18_security/4_network_security/) - Sicherheitsarchitektur und Defense-in-Depth
- [Authentifizierung](../../18_security/1_authentication/) - Details zur Integration von Identitätsanbietern
- [Infrastrukturschichten](../../2_architecture/2_infrastructure_layers/) - Übersicht über Infrastrukturkomponenten
