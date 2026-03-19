---
title: Erweiterbarkeit und Anpassung
source_sha: c28d0e1391a574d478d35f67faf167d9ce0577f26da5ae06913ae371d29bf043
---

# Erweiterbarkeit und Anpassung

Die Benutzeroberfläche der Swiss AI Hub Suite ist auf Erweiterbarkeit ausgelegt. Dies ermöglicht Organisationen,
benutzerdefinierte KI-Funktionen hinzuzufügen, proprietäre Systeme zu integrieren und die Plattform an spezifische
Geschäftsanforderungen anzupassen – und das alles unter Beibehaltung des einheitlichen Suite-Erlebnisses und ohne den
Kernplattformcode zu modifizieren.

## Architektonische Grundlagen für Erweiterbarkeit

Die Erweiterbarkeit der Suite resultiert aus bewussten Architektur-Entscheidungen, die Erweiterungspunkte von der
Kerninfrastruktur trennen. Dies ermöglicht Organisationen, Funktionen hinzuzufügen, ohne den Code zu forken oder
benutzerdefinierte Plattformversionen zu erstellen.

**Plugin-Architektur**: Services integrieren sich in die Suite über ein klar definiertes Controller-Pattern anstatt
durch direkte Code-Integration. Organisationen, die benutzerdefinierte Services implementieren, folgen den gleichen
Patterns wie native Services und stellen so sicher, dass ihre Erweiterungen eine automatische Integration mit der
Authentifizierungs-, Berechtigungs-, Internationalisierungs- und Observability-Infrastruktur erhalten.

**Standard-Integrationsverträge**: Das Controller-Pattern definiert klare Verträge für die Service-Integration.
Benutzerdefinierte Services implementieren diese Verträge, deklarieren ihre Metadaten (Name, Beschreibung, Icon,
Berechtigungen) und mounten ihre API-Endpunkte. Die Suite erkennt und integriert konforme Controller automatisch, ohne
Änderungen am Kern der Plattform zu erfordern.

**Trennung von Kern und Erweiterung**: Die Plattform trennt explizit die Kerninfrastruktur (Authentifizierung,
Autorisierung, Messaging, Persistenz) von den Service-Implementierungen. Erweiterungen nutzen die Kerninfrastruktur,
ohne sie zu modifizieren, wodurch sichergestellt wird, dass Plattform-Updates keine benutzerdefinierten Services
unterbrechen und benutzerdefinierte Services die Stabilität der Kernplattform nicht beeinträchtigen.

**Versionskompatibilität**: Der Controller-Integrationsvertrag gewährleistet die Abwärtskompatibilität über verschiedene
Plattformversionen hinweg. Services, die für eine Plattformversion implementiert wurden, funktionieren auch nach
Plattform-Updates weiterhin und schützen so die Investitionen der Organisation in benutzerdefinierte Funktionen.

## Implementierung von benutzerdefinierten Services

Organisationen können benutzerdefinierte Services implementieren, die in der Suite-Oberfläche als vollwertige
Komponenten erscheinen und sich nicht von nativen Funktionen unterscheiden lassen.

**Controller-Implementierung**: Benutzerdefinierte Services implementieren eine Controller-Klasse, die vom
Basis-Controller der Plattform erbt. Dieser Controller definiert die API-Endpunkte des Services,
Berechtigungsanforderungen und Metadaten. Die Implementierung folgt den Standard-FastAPI-Patterns, die
Python-Entwicklern vertraut sind.

**Frontend-Komponentenentwicklung**: Services, die benutzerdefinierte Benutzeroberflächen benötigen, implementieren
Frontend-Komponenten mit demselben Technologie-Stack wie die native Oberfläche – Nuxt 3, Vue 3 und PrimeVue. Diese
Komponenten greifen über automatisch generierte TypeScript-Clients auf die API-Endpunkte des benutzerdefinierten
Controllers zu, um die Typsicherheit über die Frontend-Backend-Grenze hinweg zu gewährleisten.

**Automatische Suite-Integration**: Wenn ein benutzerdefinierter Controller bei der Plattform registriert wird,
erscheint er automatisch in der dynamischen Service-Erkennung der Suite. Benutzer mit entsprechenden Berechtigungen
sehen den benutzerdefinierten Service in ihrer Seitenleisten-Navigation neben nativen Services. Icon, Name und
Beschreibung des benutzerdefinierten Services integrieren sich nahtlos in die einheitliche Oberfläche.

**Zugriff auf geteilte Infrastruktur**: Benutzerdefinierte Services erhalten automatisch Zugang zur
Plattforminfrastruktur – NATS Messaging für ereignisgesteuerte Kommunikation, MongoDB Persistenz für die
Datenspeicherung, Authentifizierung/Autorisierung für die Sicherheit, Internationalisierung für mehrsprachige
Unterstützung und Observability-Tools für Monitoring und Tracing.

## Anwendungsfälle für Erweiterungen

Organisationen implementieren verschiedene Arten von benutzerdefinierten Services, um spezifische Geschäftsanforderungen
zu erfüllen.

**Branchenspezifische Agents**: Ein Finanzdienstleistungsunternehmen könnte benutzerdefinierte Agents für die Analyse
der Einhaltung gesetzlicher Vorschriften, Finanzmodellierung oder Risikobewertung implementieren. Diese Agents
integrieren sich in den Agent-Service der Suite und erscheinen neben nativen Agents mit branchenspezifischen Workflows
und Wissensintegration.

**Proprietäre Systemintegration**: Organisationen können Services implementieren, die den Swiss AI Hub mit proprietären
Unternehmenssystemen – ERP-Systemen, benutzerdefinierten Datenbanken, Altanwendungen – verbinden. Diese
Integrations-Services könnten spezialisierte Agents bereitstellen, die mit proprietären Systemen interagieren, oder
Überwachungsschnittstellen für KI-gesteuerte Automatisierung innerhalb dieser Systeme anbieten.

**Benutzerdefinierte Analyse-Dashboards**: Organisationen mit spezifischen Berichts- oder Analyseanforderungen können
benutzerdefinierte Dashboard-Services implementieren, die Daten von Agents, Prozessen und Wissenssystemen aggregieren
und unternehmensspezifische Metriken und Visualisierungen präsentieren.

**Spezialisierte Workflows**: Prozesslastige Organisationen könnten benutzerdefinierte Prozessmanagement-Schnittstellen
implementieren, die auf spezifische Workflow-Typen zugeschnitten sind – Dokumentenfreigabe-Workflows,
Compliance-Verifizierungsprozesse, mehrstufige Überprüfungsverfahren. Diese benutzerdefinierten Schnittstellen nutzen
die Prozessautomatisierungs-Infrastruktur der Plattform, während sie domänenspezifische Ansichten präsentieren.

**Integration externer KI-Modelle**: Organisationen, die proprietäre oder spezialisierte KI-Modelle verwenden, können
benutzerdefinierte Modellintegrations-Services implementieren, die diese Modelle über die Suite zugänglich machen.
Dadurch können Agents unternehmensspezifische KI-Funktionen neben Standardmodellen nutzen.

## Workflow zur Entwicklung von Erweiterungen

Die Plattform bietet umfassende Tools und Dokumentation zur Unterstützung der Entwicklung benutzerdefinierter Services.

**Entwicklungsumgebung**: Organisationen richten lokale Entwicklungsumgebungen ein, die Produktions-Deployments
widerspiegeln. Dies ermöglicht die Entwicklung und das Testen benutzerdefinierter Services, ohne Produktionssysteme zu
beeinträchtigen. Docker Compose-Konfigurationen stellen die gesamte erforderliche Infrastruktur (Datenbanken, Message
Buses, Observability-Tools) für die lokale Entwicklung bereit.

**Codegenerierung**: Die Plattform bietet Code-Generatoren, die neue Services mit korrekter Struktur, Boilerplate-Code
und Integrations-Patterns gerüstet. Entwickler beginnen mit funktionierenden Service-Vorlagen anstatt von Grund auf neu
zu entwickeln, was die Entwicklung beschleunigt und die Einhaltung von Plattformkonventionen sicherstellt.

**Testinfrastruktur**: Benutzerdefinierte Services nutzen dieselben Test-Frameworks wie native Services. Die Plattform
stellt Test Runner bereit, die die Suite-Umgebung simulieren und so ein umfassendes Testen benutzerdefinierter Services
vor dem Deployment ermöglichen.

**Dokumentationsvorlagen**: Die Plattform enthält Dokumentationsvorlagen und Beispiele, die die Implementierung
benutzerdefinierter Services, die Entwicklung von Frontend-Komponenten, das API-Design und die Suite-Integration
demonstrieren. Diese Ressourcen beschleunigen die Entwicklung, indem sie funktionierende Beispiele gängiger Patterns
bereitstellen.

## Deployment und Distribution

Benutzerdefinierte Services werden zusammen mit der nativen Plattform deployed und werden so zu integralen Bestandteilen
der Swiss AI Hub-Installationen einer Organisation.

**Container-Verpackung**: Benutzerdefinierte Services werden als Docker-Container gemäß den Plattformkonventionen
verpackt. Diese Container werden zusammen mit nativen Plattformkomponenten deployed, was eine unabhängige Skalierung und
Versionsverwaltung ermöglicht.

**Konfigurationsmanagement**: Benutzerdefinierte Services nutzen das Konfigurationsmanagement-System der Plattform und
lesen Einstellungen aus Umgebungsvariablen und Konfigurationsdateien. Diese Integration ermöglicht konsistente
Konfigurationspraktiken über native und benutzerdefinierte Services hinweg.

**Deployment-Orchestrierung**: Organisationen erweitern Plattform-Deployment-Konfigurationen (Docker Compose-Dateien,
Kubernetes-Manifeste), um benutzerdefinierte Services einzuschließen. Deployment-Tools behandeln benutzerdefinierte
Services identisch zu nativen Services und wenden dieselben Health Checks, Monitoring- und
Lifecycle-Management-Verfahren an.

**Update-Unabhängigkeit**: Benutzerdefinierte Services können unabhängig von der nativen Plattform aktualisiert werden
(innerhalb der Versionskompatibilitätsgarantien). Organisationen können neue Versionen benutzerdefinierter Services
deployen, ohne vollständige Plattform-Updates zu benötigen, was eine agile Entwicklung benutzerdefinierter Funktionen
ermöglicht.

## Governance und Qualität

Während die Plattform Erweiterbarkeit ermöglicht, behalten Organisationen die Kontrolle darüber, welche
benutzerdefinierten Services deployed werden und wie sie sich integrieren.

**Berechtigungskontrolle**: Benutzerdefinierte Services deklarieren Berechtigungsanforderungen wie native Services.
Administratoren steuern den Zugriff von Benutzern auf benutzerdefinierte Services über dieselben Rollen- und
Berechtigungsmanagement-Oberflächen, die für native Funktionen verwendet werden.

**Qualitätsstandards**: Organisationen können Qualitäts-Gates für das Deployment benutzerdefinierter Services festlegen
– Anforderungen an Code-Reviews, Teststandards, Sicherheitsaudits, Performance-Benchmarks. Die Erweiterbarkeit der
Plattform schreibt keine niedrigeren Standards für benutzerdefinierte Services vor.

**Service-Registry**: Organisationen behalten den Überblick über deployed benutzerdefinierte Services durch dieselben
Monitoring- und Management-Oberflächen, die für native Services verwendet werden. Benutzerdefinierte Services melden den
Zustand, geben Metriken aus und generieren Audit-Logs identisch zu nativen Funktionen.

**Namespace-Isolation**: Organisationen können Namespace-Isolation implementieren, bei der benutzerdefinierte Services
für verschiedene Organisationseinheiten sich nicht gegenseitig beeinflussen. Das Berechtigungssystem gewährleistet
angemessene Zugriffsgrenzen.

## Potenzial für Community und Ökosystem

Die Erweiterbarkeitsarchitektur ermöglicht die potenzielle Entwicklung eines Ökosystems rund um die Swiss AI Hub
Plattform.

**Geteilte Erweiterungen**: Organisationen könnten benutzerdefinierte Services mit Branchenkollegen teilen, die ähnliche
Anforderungen haben. Ein benutzerdefinierter Service für die Einhaltung gesetzlicher Vorschriften im Schweizer Bankwesen
könnte mehreren Finanzinstituten zugutekommen und die gemeinsame Entwicklung fördern.

**Partner-Ökosystem**: Technologiepartner könnten benutzerdefinierte Services entwickeln, die ihre Lösungen in den Swiss
AI Hub integrieren. Dies schafft einen Marktplatz komplementärer Funktionen, die Organisationen je nach ihren
Bedürfnissen deployen können.

**Innovationsbeschleunigung**: Durch die Ermöglichung der Entwicklung benutzerdefinierter Services erlaubt die Plattform
Organisationen, schnell auf neue Anforderungen zu reagieren, ohne auf native Plattformfunktionen warten zu müssen.
Erfolgreiche benutzerdefinierte Services könnten die zukünftige native Plattformentwicklung beeinflussen.

**Wissensaustausch**: Die Community der Swiss AI Hub-Benutzer kann Implementierungs-Patterns, Best Practices und
Referenzarchitekturen für gängige benutzerdefinierte Service-Typen teilen, was die Capability-Entwicklung des gesamten
Ökosystems beschleunigt.

## Strategischer Wert für Organisationen

Die Erweiterbarkeit der Suite bietet erhebliche strategische Vorteile für Organisationen, die in KI-Fähigkeiten
investieren.

**Zukunftssichere Investition**: Während sich die KI-Technologie weiterentwickelt und neue Funktionen entstehen, können
Organisationen diese über benutzerdefinierte Services in ihr Swiss AI Hub-Deployment integrieren. Die heutige
Plattforminvestition bleibt relevant, während die Technologie fortschreitet.

**Vendor Lock-In vermeiden**: Organisationen können proprietäre KI-Funktionen, benutzerdefinierte Modelle oder
Drittanbieter-Services neben nativen Funktionen integrieren. Diese Flexibilität verhindert die Abhängigkeit von der
Feature-Roadmap oder den Technologieentscheidungen eines einzelnen Anbieters.

**Wettbewerbsdifferenzierung**: Organisationen können KI-Funktionen implementieren, die ihre einzigartigen
Geschäftsprozesse, Branchenanforderungen oder Wettbewerbsstrategien widerspiegeln. Die Suite bietet die Infrastruktur,
während Organisationen die Differenzierung steuern.

**Inkrementelle Investition**: Anstatt massiver kundenspezifischer Entwicklungsprojekte können Organisationen
fokussierte benutzerdefinierte Services implementieren, die spezifische Bedürfnisse adressieren, während sie native
Funktionen für Standardanforderungen nutzen. Dies ermöglicht inkrementelle Investitionen, die auf die Wertschöpfung
ausgerichtet sind.

**Kontrolle über die Roadmap**: Organisationen bestimmen, welche benutzerdefinierten Funktionen wann entwickelt werden,
anstatt auf Feature-Releases von Anbietern zu warten. Kritische Geschäftsanforderungen können sofort durch
kundenspezifische Entwicklung adressiert werden.

## Technische Überlegungen

Organisationen, die die Entwicklung benutzerdefinierter Services planen, sollten verschiedene technische Faktoren
berücksichtigen.

**Entwicklungsfähigkeiten**: Die Entwicklung benutzerdefinierter Services erfordert Python-Expertise für die
Backend-Implementierung und TypeScript/Vue.js-Fähigkeiten für die Frontend-Entwicklung. Organisationen sollten den
Zugang zu Entwicklern mit diesen Fähigkeiten sicherstellen oder in Schulungen investieren.

**Wartungsaufwand**: Benutzerdefinierte Services erfordern eine kontinuierliche Wartung – Bugfixes, Sicherheitsupdates,
Kompatibilität mit der Plattformentwicklung. Organisationen sollten eine langfristige Wartung planen, anstatt
benutzerdefinierte Services als einmalige Entwicklungsprojekte zu behandeln.

**Testanforderungen**: Umfassendes Testen ist für benutzerdefinierte Services unerlässlich, um sicherzustellen, dass sie
die Plattformstabilität oder -sicherheit nicht gefährden. Organisationen sollten in Testinfrastruktur und -praktiken
investieren, die für ihr Portfolio an benutzerdefinierten Services angemessen sind.

**Dokumentation**: Benutzerdefinierte Services sollten nach denselben Standards wie native Funktionen dokumentiert
werden, um sicherzustellen, dass Benutzer deren Zweck, Fähigkeiten und Nutzungsmuster verstehen. Dieser
Dokumentationsaufwand sollte in die Entwicklungsplanung einfließen.

Diese Erweiterbarkeitsarchitektur stellt sicher, dass die Swiss AI Hub Suite eine Grundlage für die langfristige
Evolution von KI-Fähigkeiten bietet. Sie ermöglicht Organisationen, vertrauensvoll in die Plattform zu investieren, da
sie wissen, dass sie diese an neue Anforderungen anpassen können, ohne das einheitliche Suite-Erlebnis zu
beeinträchtigen oder Plattformmodifikationen zu erfordern, die Updates erschweren.
