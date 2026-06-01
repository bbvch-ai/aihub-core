---
title: Netzwerkanforderungen
source_sha: 77517db5bb50f03afff9df5e32b731c2c8b10a0290e800373b85794a7d04130d
---

# Netzwerkanforderungen

Diese Seite behandelt Netzwerkkonnektivität, Firewall-Regeln und Sicherheitsanforderungen für Produktions-Deployments.

## Konnektivität zu externen Services

Die Swiss AI Hub VM verbindet sich je nach Konfiguration mit externen Services. Alle externen Verbindungen nutzen HTTPS
(Port 443).

Welche Anbieter Sie benötigen, hängt von Ihrer Deployment-Konfiguration ab.

::: details AI Service-Endpunkte
| Service         | Endpunkt                                      | Port | Zweck                                             |
| --------------- | --------------------------------------------- | ---- | ------------------------------------------------- |
| Swiss LLM Cloud | Configured via `SWISS_LLM_CLOUD_API_BASE_URL` | 443  | Texterzeugung, Embedding, Reranking, Whisper, OCR |
| Hugging Face    | `huggingface.co`                              | 443  | Modell-Downloads für selbstgehostete Inferenz     |

GPU-Deployments, die lokales vLLM ausführen, benötigen keine ausgehende Konnektivität zu LLM-Anbietern.
:::

::: details Web-Suchmaschinen (SearXNG Meta-Suche)
Der selbstgehostete SearXNG-Aggregator der Plattform fragt die untenstehenden Suchmaschinen im Auftrag von Open-WebUI
ab, wenn die Websuche aktiviert ist. Das aktive Suchmaschinen-Set ist in `infra/configs/searxng/settings.yml`
konfiguriert; siehe [Websuche](../8_web_search/) für die Begründung der Suchmaschinenauswahl und die
Anpassungsanleitung.

| Engine     | Endpunkt            | Port | Zweck                                                          |
| ---------- | ------------------- | ---- | -------------------------------------------------------------- |
| Brave      | `search.brave.com`  | 443  | Allgemeine Websuche (unabhängiger Index)                       |
| DuckDuckGo | `duckduckgo.com`    | 443  | Allgemeine Websuche (ohne Tracking, proxyt Bing)               |
| Mojeek     | `www.mojeek.com`    | 443  | Allgemeine Websuche (wirklich unabhängiger britischer Crawler) |
| Qwant      | `www.qwant.com`     | 443  | Allgemeine Websuche (Französisch/EU, DSGVO-konform)            |
| Startpage  | `www.startpage.com` | 443  | Anonymisierte Google-Ergebnisse (Niederländisch)               |
| Wikidata   | `www.wikidata.org`  | 443  | Strukturierte Daten-Abfrage                                    |
| Wikipedia  | `*.wikipedia.org`   | 443  | Enzyklopädie-Abfrage                                           |

Deaktivieren Sie die Websuche in Open-WebUI, um all diese Anforderungen zu entfernen.
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

### Identitätsanbieter-Services

Die Benutzerauthentifizierung erfordert Konnektivität zu Ihrem konfigurierten OIDC-Anbieter. Das folgende Beispiel zeigt
Microsoft Entra ID Endpunkte; ersetzen Sie diese bei Bedarf durch die Endpunkte Ihres Anbieters.

| Service            | Endpunkt                    | Zweck                                                                                   |
| ------------------ | --------------------------- | --------------------------------------------------------------------------------------- |
| Microsoft Entra ID | `login.microsoftonline.com` | OAuth2/OIDC Benutzerauthentifizierung                                                   |
| Microsoft Graph    | `graph.microsoft.com`       | Nur für SharePoint/OneDrive Pipeline-Quellen erforderlich (nicht für Authentifizierung) |

### Eingehende Verbindungen

Benutzer und Administratoren verbinden sich über diese Ports mit dem Swiss AI Hub.

| Quelle           | Ziel              | Port | Zweck                      |
| ---------------- | ----------------- | ---- | -------------------------- |
| Benutzer-Browser | VM öffentliche IP | 443  | Web-UI und Chat-Interface  |
| Administratoren  | VM öffentliche IP | 22   | Administrativer SSH-Zugang |

## Firewall-Konfiguration

Produktions-Deployments legen drei eingehende Ports offen. Dies minimiert die Angriffsfläche.

### Eingehende Regeln

Konfigurieren Sie diese Regeln in Ihrer Netzwerksicherheitsgruppe (NSG) oder Firewall:

| Priorität | Name           | Port | Protokoll | Zweck                                                             |
| --------- | -------------- | ---- | --------- | ----------------------------------------------------------------- |
| 100       | AllowHTTPS     | 443  | TCP       | Primärer Zugriff auf Swiss AI Hub Services                        |
| 110       | AllowHTTP      | 80   | TCP       | ACME/Let's Encrypt Validierung + HTTP→HTTPS-Umleitung             |
| 120       | AllowSSH       | 22   | TCP       | Administrativer Zugriff (Quell-IPs einschränken)                  |
| 65000     | DenyAllInbound | \*   | \*        | Standardmässige Ablehnung allen anderen eingehenden Datenverkehrs |

::: tip
Beschränken Sie den SSH-Zugriff (Port 22) auf bestimmte Administrator-IP-Adressen oder VPN-Bereiche, anstatt ihn von
jeder Quelle zuzulassen.
:::

### Ausgehende Regeln

Der Swiss AI Hub benötigt ausgehende Konnektivität für externe Integrationen und Updates:

| Priorität | Name       | Port | Protokoll | Zweck                                         |
| --------- | ---------- | ---- | --------- | --------------------------------------------- |
| 100       | AllowHTTPS | 443  | TCP       | API-Aufrufe an LLM-Anbieter, externe Services |
| 110       | AllowHTTP  | 80   | TCP       | Let's Encrypt Zertifikatsvalidierung          |
| 120       | AllowDNS   | 53   | UDP       | DNS-Auflösung                                 |

Die Plattform erreicht verschiedene externe APIs basierend auf Ihren Integrationen. Es sind keine zusätzlichen
ausgehenden Beschränkungen erforderlich.

## Verwandte Dokumentation

- [Deployment-Optionen](/de/docs/1_deployment_options/) - Architektur und Hosting-Strategien
- [Netzwerksicherheit](/de/docs/20_security/4_network_security/) - Sicherheitsarchitektur und Defense-in-Depth
- [Authentifizierung](/de/docs/20_security/1_authentication/) - Details zur Integration von Identitätsanbietern
- [Infrastruktur-Layer](/de/docs/2_architecture/2_infrastructure_layers/) - Übersicht der Infrastrukturkomponenten
