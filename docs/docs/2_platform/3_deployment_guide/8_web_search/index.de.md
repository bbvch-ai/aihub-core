---
title: Websuche
description: Wie Open-WebUI Ergebnisse aus dem Web über die selbst gehostete SearXNG-Instanz der Plattform abruft und wie die Engine-Liste angepasst wird.
source_sha: 0ee5f005a4a0f9ec3721039006f0468e787b023027e105492ccb21d208c07e93
---

# Websuche

Die „Websuche“-Funktion von Open-WebUI ist mit einer selbst gehosteten
[SearXNG](https://docs.searxng.org/)-Meta-Such-Instanz verbunden, die mit der Plattform ausgeliefert wird. SearXNG
leitet jede Abfrage an einen ausgewählten Satz von Upstream-Suchmaschinen weiter, führt die Ergebnisse zusammen und gibt
sie an Open-WebUI zurück, ohne dabei die Identität des Benutzers bei den Upstream-Anbietern zu protokollieren.

Diese Seite erklärt das Engine-Set, warum es gewählt wurde und wie es geändert werden kann.

## Warum SearXNG

SearXNG ist der datenschutzorientierte Suchaggregator hinter der Websuchfunktion der Plattform. Im Vergleich zu einer
einzelnen gehosteten Such-API bietet es drei Vorteile, die für ein selbst gehostetes, auf Datensouveränität fokussiertes
Deployment wichtig sind:

- **Kein Vendor Lock-in.** Die Suche ist nicht an einen einzelnen Anbieter gebunden. Engines können ohne Codeänderungen
  ausgetauscht werden.
- **Keine Kosten pro Abfrage.** SearXNG ist Open Source und selbst gehostet; es gibt keinen kostenpflichtigen
  API-Schlüssel, der erneuert werden muss.
- **Auditierbarer Egress.** Der Satz der Upstream-Engines ist in der Konfiguration aufgeführt, sodass die ausgehende
  Netzwerkfläche überprüfbar und stabil ist.

## Aktives Engine-Set

Die Plattform wird mit sieben in `infra/configs/searxng/settings.yml` aktivierten Engines ausgeliefert. Die Liste ist
datenschutzorientiert mit einer Schweizer/europäischen Ausrichtung und bevorzugt wirklich unabhängige Indizes:

| Engine     | Jurisdiktion  | Rolle                                                                 |
| ---------- | ------------- | --------------------------------------------------------------------- |
| Brave      | US            | Unabhängiger Crawler/Index, kein Tracking                             |
| DuckDuckGo | US            | Ausgereifte No-Tracking-Richtlinie; leitet Bing für die Breite weiter |
| Mojeek     | UK            | Wirklich unabhängiger Crawler (leitet Google oder Bing nicht weiter)  |
| Qwant      | Frankreich/EU | EU-Jurisdiktion, DSGVO-konform                                        |
| Startpage  | Niederlande   | Anonymisierte Google-Ergebnisse (Google-Qualität ohne Tracking)       |
| Wikidata   | Non-Profit    | Strukturierter Wissensgraph                                           |
| Wikipedia  | Non-Profit    | Enzyklopädische Suche                                                 |

Die entsprechenden ausgehenden Hostnamen sind in den [Netzwerkanforderungen](../7_network_requirements/) dokumentiert,
damit Betreiber Egress-Firewall-Regeln konfigurieren können.

## Engines, die nicht aktiviert sind

Einige Engines sind bewusst nicht im Standardset enthalten, obwohl SearXNG sie unterstützt:

- **Google, Bing.** Der direkte Zugriff auf Google und Bing tauscht wesentliche Privatsphäre gegen marginale Abdeckung.
  Die Abdeckung bleibt indirekt erhalten: Startpage leitet Google mit entferntem Tracking weiter, und DuckDuckGo leitet
  Bing weiter.
- **Yandex, Baidu, 360search.** Engines mit russischer und chinesischer Jurisdiktion liegen ausserhalb des Rahmens einer
  auf die Schweiz/EU ausgerichteten Plattform und werfen Compliance- und Zensur-Bedenken auf.
- **Spezialisierte Kategorie-Engines** (Bilder, Videos, Nachrichten-Sub-Engines, Code-Suche, Dateisuche). Die
  Websuchfunktion von Open-WebUI konsumiert derzeit nur Ergebnisse allgemeiner Kategorien, sodass spezialisierte Engines
  Egress ohne Nutzen hinzufügen würden.

Einige Engines, die wir gerne eingeschlossen hätten, können heute nicht aktiviert werden:

- **Marginalia** (🇸🇪) — Schwedischer Indie-Crawler mit starker Abdeckung von Langform-Inhalten. Standardmässig upstream
  deaktiviert und erfordert einen API-Schlüssel pro Deployment (siehe
  <https://about.marginalia-search.com/article/api/>).
- **Swisscows** (🇨🇭) — datenschutzorientierte Schweizer Suche; kein SearXNG-Engine-Modul existiert.
- **Ecosia** (🇩🇪) — leitet Bing weiter, kein natives SearXNG-Modul.
- **Kagi** — kostenpflichtiger kommerzieller Service, kein SearXNG-Modul.

## Anpassen der Engine-Liste

Die aktiven Engines werden durch die `keep_only`-Liste in `infra/configs/searxng/settings.yml` gesteuert:

```yaml
use_default_settings:
  engines:
    keep_only:
      - brave
      - duckduckgo
      - mojeek
      - qwant
      - startpage
      - wikidata
      - wikipedia
```

Um eine Engine hinzuzufügen, fügen Sie ihren Namen zur `keep_only`-Liste hinzu, generieren Sie die Compose-Dateien neu
(`make generate-compose`) und starten Sie den SearXNG-Container neu
(`docker compose -f infra/docker-compose.dev.yml --env-file .env up -d --no-deps --force-recreate searxng`). Der
vollständige Upstream-Engine-Katalog befindet sich im Container unter `/usr/local/searxng/searx/settings.yml` – mit
`docker exec searxng grep "name:" /usr/local/searxng/searx/settings.yml` werden alle verfügbaren Engines aufgelistet.

::: warning
Einige Engines (Marginalia, mehrere spezialisierte) sind upstream als `disabled: true` gekennzeichnet und erfordern
zusätzliche Konfiguration wie API-Schlüssel. Das alleinige Hinzufügen zur `keep_only`-Liste wird sie nicht aktivieren.
:::

::: tip
Wann immer Sie die Engine-Liste ändern, aktualisieren Sie die Seite [Netzwerkanforderungen](../7_network_requirements/),
damit die Betreiber die neuen ausgehenden Hostnamen sehen.
:::

## Websuche vollständig deaktivieren

Um die Websuche von der Plattform zu entfernen, setzen Sie `ENABLE_WEB_SEARCH: False` im Open-WebUI-Umgebungsblock in
`infra/deployment/templates/docker-compose.yml.j2`, generieren Sie die Compose-Dateien neu und erstellen Sie Open-WebUI
neu. Der `searxng`-Service kann dann auch aus dem Template entfernt werden, falls er nicht mehr benötigt wird; dies
eliminiert alle websuchebezogenen ausgehenden Netzwerkanforderungen.
