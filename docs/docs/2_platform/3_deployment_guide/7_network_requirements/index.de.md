---
title: Netzwerkanforderungen
source_sha: 4250941683c8b405f5dd0a5e83617f248a88500b2d120133d8f5353f4938a4a8
---

# Netzwerkanforderungen

Diese Seite behandelt Netzwerkkonnektivität, Firewall-Regeln und Sicherheitsanforderungen für Produktions-Deployments.

## Konnektivität zu externen Services

Die Swiss AI Hub VM verbindet sich je nach Konfiguration mit externen Services. Alle externen Verbindungen verwenden
HTTPS (Port 443).

Welche Provider Sie benötigen, hängt von Ihrer Deployment-Konfiguration ab.

::: details KI-Service-Endpunkte
| Service         | Endpunkt                                      | Port | Zweck                                             |
| --------------- | --------------------------------------------- | ---- | ------------------------------------------------- |
| Swiss LLM Cloud | Configured via `SWISS_LLM_CLOUD_API_BASE_URL` | 443  | Texterzeugung, Embedding, Reranking, Whisper, OCR |
| Hugging Face    | `huggingface.co`                              | 443  | Modelldownloads für selbst gehostete Inferenz     |

GPU-Deployments, die lokales vLLM ausführen, benötigen keine ausgehende Konnektivität zu LLM-Providern.
:::

::: details Web-Suchmaschinen (SearXNG Meta-Suche)
Der selbst gehostete SearXNG-Aggregator der Plattform fragt die unten aufgeführten Suchmaschinen im Auftrag von
Open-WebUI ab, wenn die Websuche aktiviert ist. Der aktive Engine-Satz ist in `infra/configs/searxng/settings.yml`
konfiguriert; siehe [Websuche](../8_web_search/) für die Begründung der Engine-Auswahl und die Anpassungsanleitung.

| Engine     | Endpunkt            | Port | Zweck                                                          |
| ---------- | ------------------- | ---- | -------------------------------------------------------------- |
| Brave      | `search.brave.com`  | 443  | Allgemeine Websuche (unabhängiger Index)                       |
| DuckDuckGo | `duckduckgo.com`    | 443  | Allgemeine Websuche (ohne Tracking, proxyed Bing)              |
| Mojeek     | `www.mojeek.com`    | 443  | Allgemeine Websuche (wirklich unabhängiger britischer Crawler) |
| Qwant      | `www.qwant.com`     | 443  | Allgemeine Websuche (Französisch/EU, DSGVO-konform)            |
| Startpage  | `www.startpage.com` | 443  | Anonymisierte Google-Ergebnisse (Niederländisch)               |
| Wikidata   | `www.wikidata.org`  | 443  | Strukturierte Datenabfrage                                     |
| Wikipedia  | `*.wikipedia.org`   | 443  | Enzyklopädie-Abfrage                                           |

Deaktivieren Sie die Websuche in Open-WebUI, um all diese Anforderungen fallen zu lassen.
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

### Identitätsprovider-Services

Die Benutzerauthentifizierung erfordert Konnektivität zu Ihrem konfigurierten OIDC-Provider. Das folgende Beispiel zeigt
Microsoft Entra ID-Endpunkte; ersetzen Sie diese bei Bedarf durch die Endpunkte Ihres Providers.

| Service            | Endpunkt                    | Zweck                                                                                   |
| ------------------ | --------------------------- | --------------------------------------------------------------------------------------- |
| Microsoft Entra ID | `login.microsoftonline.com` | OAuth2/OIDC Benutzerauthentifizierung                                                   |
| Microsoft Graph    | `graph.microsoft.com`       | Nur für SharePoint/OneDrive Pipeline-Quellen erforderlich (nicht für Authentifizierung) |

### Eingehende Verbindungen

Benutzer und Administratoren verbinden sich über diese Ports mit dem Swiss AI Hub.

| Quelle           | Ziel              | Port | Zweck                       |
| ---------------- | ----------------- | ---- | --------------------------- |
| Benutzer-Browser | VM öffentliche IP | 443  | Web-UI und Chat-Oberfläche  |
| Administratoren  | VM öffentliche IP | 22   | Administrativer SSH-Zugriff |

## Firewall-Konfiguration

Produktions-Deployments legen drei eingehende Ports offen. Dies minimiert die Angriffsfläche.

### Eingehende Regeln

Konfigurieren Sie diese Regeln in Ihrer Netzwerksicherheitsgruppe (NSG) oder Firewall:

| Priorität | Name           | Port | Protokoll | Zweck                                                              |
| --------- | -------------- | ---- | --------- | ------------------------------------------------------------------ |
| 100       | AllowHTTPS     | 443  | TCP       | Primärer Zugriff auf Swiss AI Hub Services                         |
| 110       | AllowHTTP      | 80   | TCP       | ACME/Let's Encrypt Validierung + HTTP→HTTPS-Weiterleitung          |
| 120       | AllowSSH       | 22   | TCP       | Administrativer Zugriff (Quell-IPs einschränken)                   |
| 65000     | DenyAllInbound | \*   | \*        | Standardmässiges Verweigern jeglichen anderen eingehenden Traffics |

::: tip
Beschränken Sie den SSH-Zugriff (Port 22) auf bestimmte Administrator-IP-Adressen oder VPN-Bereiche, anstatt ihn von
jeder Quelle zuzulassen.
:::

### Ausgehende Regeln

Der Swiss AI Hub benötigt ausgehende Konnektivität für externe Integrationen und Updates:

| Priorität | Name       | Port | Protokoll | Zweck                                         |
| --------- | ---------- | ---- | --------- | --------------------------------------------- |
| 100       | AllowHTTPS | 443  | TCP       | API-Aufrufe an LLM-Provider, externe Services |
| 110       | AllowHTTP  | 80   | TCP       | Let's Encrypt Zertifikatsvalidierung          |
| 120       | AllowDNS   | 53   | UDP       | DNS-Auflösung                                 |

Die Plattform erreicht verschiedene externe APIs basierend auf Ihren Integrationen. Es sind keine zusätzlichen
ausgehenden Beschränkungen erforderlich.

## Verwandte Dokumentation

- [Deployment-Optionen](/de/docs/1_deployment_options/) - Architektur und Hosting-Strategien
- [Netzwerksicherheit](/de/docs/20_security/4_network_security/) - Sicherheitsarchitektur und Defense-in-Depth
- [Authentifizierung](/de/docs/20_security/1_authentication/) - Details zur Identitätsprovider-Integration
- [Infrastruktur-Ebenen](/de/docs/1_vision_and_positioning/4_infrastructure_layers/) - Überblick über
  Infrastrukturkomponenten
