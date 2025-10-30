---
title: Chat-Schnittstelle
source_sha: 37f70424320ae433e5af4732cc3f2d10bb26f97d1976c763fd4d59e3420a097e
---

# Chat-Schnittstelle

Der Swiss AI Hub nutzt **Open WebUI** als seine primäre Chat-Schnittstelle. Open WebUI ist ein Open-Source-Projekt mit
einem umfassenden Funktionsumfang, der Dokumentenverwaltung, Benutzerverwaltung, Tools, Sprachinteraktion und
kollaborative Funktionen umfasst. Anstatt eine eigene Chat-Schnittstelle zu entwickeln, integriert die Plattform diese
bestehende Lösung und erweitert sie mit benutzerdefinierten Funktionen.

## Warum eine bestehende Lösung verwenden?

Der Aufbau einer produktionsreifen Chat-Schnittstelle erfordert erheblichen Entwicklungsaufwand. Open WebUI bietet diese
Funktionalität bereits mit einer aktiven Wartungsgemeinschaft. Das Swiss AI Hub Team kann sich auf Fähigkeiten
konzentrieren, die spezifisch für die Bereitstellung von KI in Unternehmen sind, anstatt Standard-Chat-Funktionen neu zu
erstellen.

Während sich Open WebUI weiterentwickelt, erhält der Swiss AI Hub diese Verbesserungen durch regelmäßige Updates. Die
Plattform profitiert von der gemeinschaftsgesteuerten Entwicklung, Dokumentation und Bereitstellungsmustern, ohne
Ressourcen für die Pflege der grundlegenden Chat-Infrastruktur aufwenden zu müssen.

## Benutzerdefinierte Erweiterungen

Der Swiss AI Hub erweitert die Funktionalität von Open WebUI auf drei Hauptarten.

Die Schnittstelle ist direkt in die Swiss AI Hub Suite eingebettet, anstatt als separate Anwendung zu laufen. Benutzer
greifen über eine vereinheitlichte Navigation auf Chat-Funktionen zu, ohne den Kontext wechseln oder sich neu
authentifizieren zu müssen.

Wenn KI-Antworten aus organisationsinternen Wissensdatenbanken stammen, können Benutzer die spezifischen Dokumente und
Passagen einsehen, die die Antwort beeinflusst haben. Diese Quellenattribution ermöglicht die Überprüfung von
KI-generierten Inhalten.

Benutzerdefiniertes Tracing zeigt die schrittweise Agentenausführung, einschließlich Argumentationsketten, Tool-Aufrufen
und Entscheidungspunkten. Diese Sichtbarkeit unterstützt das Debugging und die Anforderungen an die Einhaltung
gesetzlicher Vorschriften.

## Überlegungen zur Bereitstellung

Organisationen, die den Swiss AI Hub nutzen, vermeiden die Kosten für den Aufbau und die Wartung einer
benutzerdefinierten Chat-Schnittstelle. Entwicklungsressourcen fließen in unternehmensspezifische Anforderungen statt in
Commodity-Funktionalität.

Die Open-Source-Grundlage bietet Flexibilität. Organisationen können die Chat-Schnittstelle forken oder modifizieren,
wenn sich die Anforderungen ändern. Die Lebensfähigkeit der Plattform hängt nicht von der Roadmap eines einzelnen
Anbieters ab.

Die bestehenden Produktionsimplementierungen und die aktive Community reduzieren das technische Risiko im Vergleich zu
einer Eigenentwicklung. Organisationen setzen bewährte Technologie mit etablierten Mustern ein.

## Dokumentationsstruktur

Dieser Abschnitt behandelt die Integration der Chat-Schnittstelle aus verschiedenen Blickwinkeln:

- [Integrationsarchitektur](11_integration_architecture/) erklärt, wie Open WebUI mit der Suite verbunden ist und die
  Kommunikation handhabt
- [Quellenattribution](3_chat_with_your_data/) beschreibt die benutzerdefinierten Erweiterungen für die Sichtbarkeit der
  Wissensabfrage
- [Beobachtbarkeit](10_observability/) behandelt die Ausführungsverfolgung und Workflow-Transparenz
- [Funktionsübersicht](1_feature_overview/) katalogisiert die von Open WebUI geerbten Funktionen
- [Strategische Begründung](12_strategic_rationale/) analysiert die Entscheidung, eine bestehende Lösung zu integrieren
