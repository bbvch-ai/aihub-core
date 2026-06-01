---
title: Erweiterbarkeit und Anpassung
source_sha: "eb206c9118f83ca12d29616aa160088adec48f59c055247c5a189b039390633d"
---
```

# Erweiterbarkeit und Anpassung

Die Benutzeroberfläche der Swiss AI Hub Suite ist auf Erweiterbarkeit ausgelegt. Dies ermöglicht Unternehmen, massgeschneiderte KI-Funktionen hinzuzufügen, proprietäre Systeme zu integrieren und die Plattform an spezifische Geschäftsanforderungen anzupassen – und das alles, ohne das einheitliche Suite-Erlebnis zu beeinträchtigen oder den Kerncode der Plattform zu modifizieren.

::: tip Hinweis zur Lizenzierung
Das hier beschriebene Erweiterungsmodell – benutzerdefinierte Services und Ihre eigenen Komponenten, die *auf* der Plattform aufgebaut sind – lässt Ihren Service-Code unter der Lizenz Ihrer Wahl; Sie modifizieren die Plattform selbst nicht. Die gebündelte UI (`packages/web`) ist jedoch unter der Lizenz **AGPL-3.0** lizenziert. Wenn Sie diese UI selbst modifizieren und als Netzwerkdienst anbieten, verlangt AGPL-3.0 von Ihnen, diese UI-Modifikationen unter derselben Lizenz zu veröffentlichen. Weitere Details finden Sie unter [Warum Backend und UI unterschiedliche Lizenzen verwenden](../../../4_ecosystem/3_certification/2_sdk_licensing/) und [LICENSES.md](https://github.com/bbvch-ai/aihub-core/blob/main/LICENSES.md).
:::

## Architektonische Grundlagen für die Erweiterbarkeit

Die Erweiterbarkeit der Suite resultiert aus bewussten Architektur-Entscheidungen, die Erweiterungspunkte von der Kerninfrastruktur trennen. Dies ermöglicht Unternehmen, Funktionen hinzuzufügen, ohne die Codebasis zu forken oder benutzerdefinierte Plattformversionen zu erstellen.

**Plugin-Architektur**: Services integrieren sich in die Suite über ein klar definiertes Controller-Muster statt durch direkte Code-Integration. Unternehmen, die benutzerdefinierte Services implementieren, folgen denselben Mustern wie native Services, wodurch sichergestellt wird, dass ihre Erweiterungen automatisch in die Infrastruktur für Authentifizierung, Berechtigungen, Internationalisierung und Observability integriert werden.

**Standard-Integrationsverträge**: Das Controller-Muster definiert klare Verträge für die Service-Integration. Benutzerdefinierte Services implementieren diese Verträge, deklarieren ihre Metadaten (Name, Beschreibung, Icon, Berechtigungen) und binden ihre API-Endpunkte ein. Die Suite erkennt und integriert konforme Controller automatisch, ohne dass Modifikationen an der Kernplattform erforderlich sind.

**Trennung von Kern und Erweiterung**: Die Plattform trennt explizit die Kerninfrastruktur (Authentifizierung, Autorisierung, Messaging, Persistenz) von den Service-Implementierungen. Erweiterungen nutzen die Kerninfrastruktur, ohne sie zu modifizieren, wodurch sichergestellt wird, dass Plattform-Updates benutzerdefinierte Services nicht beeinträchtigen und benutzerdefinierte Services die Stabilität der Kernplattform nicht gefährden.

**Versionskompatibilität**: Der Controller-Integrationsvertrag gewährleistet Abwärtskompatibilität über verschiedene Plattformversionen hinweg. Services, die für eine Plattformversion implementiert wurden, funktionieren weiterhin, wenn die Plattform aktualisiert wird, was die Investition des Unternehmens in benutzerdefinierte Funktionen schützt.

## Implementierung benutzerdefinierter Services

Unternehmen können benutzerdefinierte Services implementieren, die als First-Class-Citizens in der Suite-Oberfläche erscheinen und von nativen Funktionen nicht zu unterscheiden sind.

**Controller-Implementierung**: Benutzerdefinierte Services implementieren eine Controller-Klasse, die vom Basis-Controller der Plattform erbt. Dieser Controller definiert die API-Endpunkte des Services, Berechtigungsanforderungen und Metadaten. Die Implementierung folgt Standard-FastAPI-Mustern, die Python-Entwicklern vertraut sind.

**Frontend-Komponentenentwicklung**: Services, die benutzerdefinierte Benutzeroberflächen benötigen, implementieren Frontend-Komponenten unter Verwendung desselben Technologie-Stacks wie die native Schnittstelle – Nuxt 3, Vue 3 und PrimeVue. Diese Komponenten greifen über automatisch generierte TypeScript-Clients auf die API-Endpunkte des benutzerdefinierten Controllers zu, wodurch Typsicherheit über die Frontend-Backend-Grenze hinweg gewährleistet wird.

**Automatische Suite-Integration**: Wenn ein benutzerdefinierter Controller bei der Plattform registriert wird, erscheint er automatisch in der dynamischen Service-Erkennung der Suite. Benutzer mit den entsprechenden Berechtigungen sehen den benutzerdefinierten Service in ihrer Seitenleisten-Navigation neben den nativen Services. Das Icon, der Name und die Beschreibung des benutzerdefinierten Services integrieren sich nahtlos in die einheitliche Benutzeroberfläche.

**Zugriff auf gemeinsame Infrastruktur**: Benutzerdefinierte Services erhalten automatisch Zugriff auf die Plattform-Infrastruktur – NATS Messaging für ereignisgesteuerte Kommunikation, MongoDB Persistenz für die Datenspeicherung, Authentifizierung/Autorisierung für Sicherheit, Internationalisierung für mehrsprachige Unterstützung und Observability-Tools für Monitoring und Tracing.

## Anwendungsfälle für Erweiterungen

Unternehmen implementieren verschiedene Arten von benutzerdefinierten Services, um spezifische Geschäftsanforderungen zu erfüllen.

**Branchenspezifische Agents**: Ein Finanzdienstleistungsunternehmen könnte benutzerdefinierte Agents für die Analyse der Einhaltung gesetzlicher Vorschriften, Finanzmodellierung oder Risikobewertung implementieren. Diese Agents integrieren sich in den Agent-Service der Suite und erscheinen neben nativen Agents mit branchenspezifischen Workflows und Wissensintegration.

**Proprietäre Systemintegration**: Unternehmen können Services implementieren, die den Swiss AI Hub mit proprietären Unternehmenssystemen – ERP-Systemen, kundenspezifischen Datenbanken, Legacy-Anwendungen – verbinden. Diese Integrations-Services könnten spezialisierte Agents bereitstellen, die mit proprietären Systemen interagieren, oder Monitoring-Schnittstellen für KI-gesteuerte Automatisierung innerhalb dieser Systeme anbieten.

**Benutzerdefinierte Analyse-Dashboards**: Unternehmen mit spezifischen Berichts- oder Analyseanforderungen können benutzerdefinierte Dashboard-Services implementieren, die Daten von Agents, Prozessen und Wissenssystemen aggregieren und unternehmensspezifische Metriken und Visualisierungen präsentieren.

**Spezialisierte Workflows**: Prozessintensive Unternehmen könnten benutzerdefinierte Prozessmanagement-Schnittstellen implementieren, die auf spezifische Workflow-Typen zugeschnitten sind – Dokumenten-Genehmigungs-Workflows, Compliance-Verifizierungsprozesse, mehrstufige Überprüfungsverfahren. Diese benutzerdefinierten Schnittstellen nutzen die Prozessautomatisierungs-Infrastruktur der Plattform, während sie domänenspezifische Ansichten präsentieren.

**Integration externer KI-Modelle**: Unternehmen, die proprietäre oder spezialisierte KI-Modelle verwenden, können benutzerdefinierte Modellintegrations-Services implementieren, die diese Modelle über die Suite zugänglich machen, wodurch Agents unternehmensspezifische KI-Funktionen neben Standardmodellen nutzen können.

## Workflow für die Erweiterungsentwicklung

Die Plattform bietet umfassende Tools und Dokumentationen zur Unterstützung der Entwicklung benutzerdefinierter Services.

**Entwicklungsumgebung**: Unternehmen richten lokale Entwicklungsumgebungen ein, die Produktions-Deployments widerspiegeln. Dies ermöglicht die Entwicklung und das Testen benutzerdefinierter Services, ohne Produktionssysteme zu beeinträchtigen. Docker Compose-Konfigurationen stellen die gesamte erforderliche Infrastruktur (Datenbanken, Message Buses, Observability-Tools) für die lokale Entwicklung bereit.

**Code-Generierung**: Die Plattform bietet Code-Generatoren, die neue Services mit der korrekten Struktur, Boilerplate-Code und Integrationsmustern gerüsten. Entwickler beginnen mit funktionierenden Service-Vorlagen, anstatt von Grund auf neu zu entwickeln, was die Entwicklung beschleunigt und die Einhaltung von Plattform-Konventionen sicherstellt.

**Testinfrastruktur**: Benutzerdefinierte Services nutzen dieselben Test-Frameworks wie native Services. Die Plattform stellt Test-Runner bereit, die die Suite-Umgebung simulieren und so ein umfassendes Testen benutzerdefinierter Services vor dem Deployment ermöglichen.

**Dokumentationsvorlagen**: Die Plattform enthält Dokumentationsvorlagen und Beispiele, die die Implementierung benutzerdefinierter Services, die Frontend-Komponentenentwicklung, das API-Design und die Suite-Integration demonstrieren. Diese Ressourcen beschleunigen die Entwicklung, indem sie funktionierende Beispiele gängiger Muster bereitstellen.

## Deployment und Distribution

Benutzerdefinierte Services werden zusammen mit der nativen Plattform deployed und werden so zu integralen Bestandteilen der Swiss AI Hub-Installationen von Unternehmen.

**Container-Verpackung**: Benutzerdefinierte Services werden als Docker-Container nach den Plattformkonventionen verpackt. Diese Container werden zusammen mit nativen Plattformkomponenten deployed, was eine unabhängige Skalierung und Versionsverwaltung ermöglicht.

**Konfigurationsmanagement**: Benutzerdefinierte Services nutzen das Konfigurationsmanagement-System der Plattform und lesen Einstellungen aus Umgebungsvariablen und Konfigurationsdateien. Diese Integration ermöglicht konsistente Konfigurationspraktiken über native und benutzerdefinierte Services hinweg.

**Deployment-Orchestrierung**: Unternehmen erweitern die Plattform-Deployment-Konfigurationen (Docker Compose-Dateien, Kubernetes-Manifeste), um benutzerdefinierte Services einzuschliessen. Deployment-Tools behandeln benutzerdefinierte Services identisch mit nativen Services und wenden dieselben Health Checks, Monitoring- und Lifecycle-Management-Verfahren an.

**Update-Unabhängigkeit**: Benutzerdefinierte Services können unabhängig von der nativen Plattform aktualisiert werden (innerhalb der Garantien für Versionskompatibilität). Unternehmen können neue benutzerdefinierte Service-Versionen deployen, ohne vollständige Plattform-Updates zu benötigen, was eine agile Entwicklung benutzerdefinierter Funktionen ermöglicht.

## Governance und Qualität

Während die Plattform Erweiterbarkeit ermöglicht, behalten Unternehmen die Kontrolle darüber, welche benutzerdefinierten Services deployed werden und wie sie integriert werden.

**Berechtigungssteuerung**: Benutzerdefinierte Services deklarieren Berechtigungsanforderungen wie native Services. Administratoren steuern den Zugriff von Benutzern auf benutzerdefinierte Services über dieselben Rollen- und Berechtigungsmanagement-Schnittstellen, die für native Funktionen verwendet werden.

**Qualitätsstandards**: Unternehmen können Qualitätstore für das Deployment benutzerdefinierter Services etablieren – Anforderungen an Code-Reviews, Teststandards, Sicherheitsaudits, Performance-Benchmarks. Die Erweiterbarkeit der Plattform schreibt keine niedrigeren Standards für benutzerdefinierte Services vor.

**Service-Registry**: Unternehmen behalten über dieselben Monitoring- und Management-Schnittstellen, die für native Services verwendet werden, den Überblick über deployed benutzerdefinierte Services. Benutzerdefinierte Services melden den Zustand, stellen Metriken bereit und generieren Audit-Logs identisch mit nativen Funktionen.

**Namespace-Isolation**: Unternehmen können Namespace-Isolation implementieren, bei der benutzerdefinierte Services für verschiedene Organisationseinheiten sich nicht gegenseitig stören. Das Berechtigungssystem stellt angemessene Zugriffsbarrieren sicher.

## Community- und Ökosystem-Potenzial

Die Erweiterbarkeitsarchitektur ermöglicht die potenzielle Entwicklung eines Ökosystems rund um die Swiss AI Hub Plattform.

**Geteilte Erweiterungen**: Unternehmen könnten benutzerdefinierte Services mit Branchenkollegen teilen, die ähnliche Anforderungen haben. Ein benutzerdefinierter Service für die Einhaltung gesetzlicher Vorschriften im Schweizer Bankwesen könnte mehreren Finanzinstituten zugutekommen und die kollaborative Entwicklung fördern.

**Partner-Ökosystem**: Technologiepartner könnten benutzerdefinierte Services entwickeln, die ihre Lösungen mit dem Swiss AI Hub integrieren. Dadurch entsteht ein Marktplatz komplementärer Funktionen, die Unternehmen je nach ihren Bedürfnissen bereitstellen können.

**Innovationsbeschleunigung**: Durch die Ermöglichung der Entwicklung benutzerdefinierter Services erlaubt die Plattform Unternehmen, schnell auf neue Anforderungen zu reagieren, ohne auf native Plattformfunktionen warten zu müssen. Erfolgreiche benutzerdefinierte Services könnten die zukünftige Entwicklung der nativen Plattform beeinflussen.

**Wissensaustausch**: Die Community der Swiss AI Hub-Benutzer kann Implementierungsmuster, Best Practices und Referenzarchitekturen für gängige benutzerdefinierte Service-Typen austauschen, was die Fähigkeitsentwicklung des gesamten Ökosystems beschleunigt.

## Strategischer Wert für Unternehmen

Die Erweiterbarkeit der Suite bietet Unternehmen, die in KI-Funktionen investieren, erhebliche strategische Vorteile.

**Zukunftssichere Investition**: Während sich die KI-Technologie weiterentwickelt und neue Funktionen entstehen, können Unternehmen diese über benutzerdefinierte Services in ihr Swiss AI Hub Deployment integrieren. Die heutige Plattforminvestition bleibt relevant, während die Technologie fortschreitet.

**Vermeidung von Vendor Lock-in**: Unternehmen können proprietäre KI-Funktionen, benutzerdefinierte Modelle oder Drittanbieter-Services neben nativen Funktionen integrieren. Diese Flexibilität verhindert die Abhängigkeit von der Feature-Roadmap oder den Technologieentscheidungen eines einzelnen Anbieters.

**Wettbewerbsdifferenzierung**: Unternehmen können KI-Funktionen implementieren, die ihre einzigartigen Geschäftsprozesse, Branchenanforderungen oder Wettbewerbsstrategien widerspiegeln. Die Suite bietet die Infrastruktur, während Unternehmen die Differenzierung steuern.

**Inkrementelle Investition**: Anstatt massiver kundenspezifischer Entwicklungsprojekte können Unternehmen zielgerichtete benutzerdefinierte Services implementieren, die spezifische Bedürfnisse adressieren, während sie native Funktionen für Standardanforderungen nutzen. Dies ermöglicht inkrementelle Investitionen, die auf die Wertschöpfung abgestimmt sind.

**Kontrolle über die Roadmap**: Unternehmen bestimmen, welche benutzerdefinierten Funktionen wann entwickelt werden sollen, anstatt auf Feature-Releases von Anbietern zu warten. Kritische Geschäftsanforderungen können durch kundenspezifische Entwicklung sofort adressiert werden.

## Technische Überlegungen

Unternehmen, die die Entwicklung benutzerdefinierter Services planen, sollten mehrere technische Faktoren berücksichtigen.

**Entwicklungskompetenzen**: Die Entwicklung benutzerdefinierter Services erfordert Python-Expertise für die Backend-Implementierung und TypeScript-/Vue.js-Kenntnisse für die Frontend-Entwicklung. Unternehmen sollten den Zugang zu Entwicklern mit diesen Fähigkeiten sicherstellen oder in Schulungen investieren.

**Wartungsaufwand**: Benutzerdefinierte Services erfordern fortlaufende Wartung – Bugfixes, Sicherheitsupdates, Kompatibilität mit der Plattformentwicklung. Unternehmen sollten langfristige Wartung planen, anstatt benutzerdefinierte Services als einmalige Entwicklungsprojekte zu behandeln.

**Testanforderungen**: Umfassende Tests sind für benutzerdefinierte Services unerlässlich, um sicherzustellen, dass sie die Plattformstabilität oder -sicherheit nicht beeinträchtigen. Unternehmen sollten in Testinfrastruktur und -praktiken investieren, die für ihr Portfolio an benutzerdefinierten Services angemessen sind.

**Dokumentation**: Benutzerdefinierte Services sollten nach denselben Standards wie native Funktionen dokumentiert werden, um sicherzustellen, dass Benutzer deren Zweck, Funktionen und Nutzungsmuster verstehen. Dieser Dokumentationsaufwand sollte in die Entwicklungsplanung einfliessen.

Diese Erweiterbarkeitsarchitektur stellt sicher, dass die Swiss AI Hub Suite eine Grundlage für die langfristige Entwicklung von KI-Funktionen bietet. Sie ermöglicht Unternehmen, vertrauensvoll in die Plattform zu investieren, da sie wissen, dass sie diese an neue Anforderungen anpassen können, ohne das einheitliche Suite-Erlebnis zu beeinträchtigen oder Plattformmodifikationen vornehmen zu müssen, die Updates erschweren.
