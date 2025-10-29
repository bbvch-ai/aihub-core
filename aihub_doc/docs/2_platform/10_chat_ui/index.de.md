---
title: Chat-Interface
source_sha: "6c8dd5e279dee367e880c211672591704247d147d7253c61bce9b03ce3e1a89c"
---

# Chat-Interface

Der Swiss AI Hub verwendet **Open WebUI** als primäres Chat-Interface. Open WebUI ist ein Open-Source-Projekt mit einem
umfassenden Funktionsumfang, der Dokumentenverwaltung, Benutzerverwaltung, Tools, Sprachinteraktion und Kollaborationsfunktionen
umfasst. Anstatt ein benutzerdefiniertes Chat-Interface zu entwickeln, integriert die Plattform diese bestehende Lösung
und erweitert sie um benutzerdefinierte Funktionen.

## Warum eine bestehende Lösung verwenden?

Der Aufbau eines produktionsreifen Chat-Interfaces erfordert erheblichen Entwicklungsaufwand. Open WebUI bietet diese
Funktionalität bereits mit einer aktiven Wartungsgemeinschaft. Das Swiss AI Hub-Team kann sich auf Fähigkeiten konzentrieren,
die spezifisch für die Bereitstellung von Unternehmens-KI sind, anstatt Standard-Chat-Funktionen neu zu erstellen.

Mit der Weiterentwicklung von Open WebUI erhält der Swiss AI Hub diese Verbesserungen durch regelmäßige Updates. Die
Plattform profitiert von gemeinschaftsgetriebener Entwicklung, Dokumentation und Bereitstellungsmustern, ohne Ressourcen
für die Wartung der grundlegenden Chat-Infrastruktur aufwenden zu müssen.

## Benutzerdefinierte Erweiterungen

Der Swiss AI Hub erweitert die Funktionalität von Open WebUI auf drei Hauptarten.

Das Interface ist direkt in die Swiss AI Hub-Suite eingebettet, anstatt als separate Anwendung zu laufen. Benutzer greifen
über eine einheitliche Navigation auf Chat-Funktionen zu, ohne den Kontext wechseln oder sich erneut authentifizieren
zu müssen.

Wenn KI-Antworten auf organisationsinternen Wissensdatenbanken basieren, können Benutzer die spezifischen Dokumente und
Passagen einsehen, die die Antwort beeinflusst haben. Diese Quellenangabe ermöglicht die Verifizierung von KI-generierten
Inhalten.

Benutzerdefiniertes Tracing zeigt die schrittweise Agenten-Ausführung, einschließlich Argumentationsketten, Tool-Aufrufen
und Entscheidungspunkten. Diese Transparenz unterstützt das Debugging und die Einhaltung regulatorischer Anforderungen.

## Bereitstellungsüberlegungen

Organisationen, die den Swiss AI Hub nutzen, vermeiden die Kosten für den Aufbau und die Wartung eines benutzerdefinierten
Chat-Interfaces. Entwicklungsressourcen fließen in unternehmensspezifische Anforderungen statt in Standardfunktionen.

Die Open-Source-Grundlage bietet Flexibilität. Organisationen können das Chat-Interface forken oder ändern, wenn sich die
Anforderungen ändern. Die Lebensfähigkeit der Plattform hängt nicht von der Roadmap eines einzelnen Anbieters ab.

Die bestehenden Produktionsimplementierungen und die aktive Community reduzieren das technische Risiko im Vergleich zur
kundenspezifischen Entwicklung. Organisationen setzen bewährte Technologie mit etablierten Mustern ein.

## Dokumentationsstruktur

Dieser Abschnitt behandelt die Integration des Chat-Interfaces aus verschiedenen Blickwinkeln:

- [Integrationsarchitektur](11_integration_architecture/) erklärt, wie Open WebUI mit der Suite
  verbunden ist und die Kommunikation handhabt
- [Quellenangabe](3_chat_with_your_data/) beschreibt die benutzerdefinierten Erweiterungen
  für die Sichtbarkeit der Wissensabfrage
- [Beobachtbarkeit](10_observability/) behandelt die Ausführungsverfolgung und die
  Transparenz von Workflows
- [Funktionsübersicht](1_feature_overview/) katalogisiert die von Open WebUI übernommenen
  Funktionen
- [Strategische Begründung](12_strategic_rationale/) analysiert die Entscheidung zur
  Integration einer bestehenden Lösung
