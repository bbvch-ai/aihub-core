---
title: Erweiterbarkeit und Anpassung
index: 5
source_sha: "c0cf9a3c2de66993ca6f2945eb957d16bd079414e3d68f4b2e8d78046f8ce9d1"
---

# Erweiterbarkeit und Anpassung

Die Oberfläche der Swiss AI Hub Suite ist auf Erweiterbarkeit ausgelegt. Sie ermöglicht es Organisationen, eigene KI-Funktionen hinzuzufügen,
proprietäre Systeme zu integrieren und die Plattform an spezifische Geschäftsanforderungen anzupassen – und das alles unter Beibehaltung des
einheitlichen Suite-Erlebnisses und ohne Änderungen am Kerncode der Plattform.

## Architektonische Grundlagen für die Erweiterbarkeit

Die Erweiterbarkeit der Suite ergibt sich aus bewussten architektonischen Entscheidungen, die Erweiterungspunkte von der Kerninfrastruktur trennen. Dies ermöglicht es Organisationen, Funktionen hinzuzufügen, ohne die Codebasis zu forken oder benutzerdefinierte Plattformversionen zu erstellen.

**Plugin-Architektur**: Dienste werden über ein klar definiertes Controller-Muster in die Suite integriert, anstatt über eine direkte Code-Integration. Organisationen, die kundenspezifische Dienste implementieren, folgen denselben Mustern wie native Dienste, wodurch sichergestellt wird, dass ihre Erweiterungen automatisch in die Authentifizierungs-, Berechtigungs-, Internationalisierungs- und Observability-Infrastruktur integriert werden.

**Standard-Integrationsverträge**: Das Controller-Muster definiert klare Verträge für die Dienstintegration. Kundenspezifische Dienste implementieren diese Verträge, deklarieren ihre Metadaten (Name, Beschreibung, Icon, Berechtigungen) und stellen ihre API-Endpunkte bereit. Die Suite erkennt und integriert automatisch konforme Controller, ohne dass Änderungen an der Kernplattform erforderlich sind.

**Trennung von Kern und Erweiterung**: Die Plattform trennt explizit die Kerninfrastruktur (Authentifizierung, Autorisierung, Messaging, Persistenz) von den Dienstimplementierungen. Erweiterungen nutzen die Kerninfrastruktur, ohne sie zu modifizieren, wodurch sichergestellt wird, dass Plattform-Updates kundenspezifische Dienste nicht beeinträchtigen und kundenspezifische Dienste die Stabilität der Kernplattform nicht gefährden.

**Versionskompatibilität**: Der Controller-Integrationsvertrag behält die Abwärtskompatibilität über verschiedene Plattformversionen hinweg bei. Dienste, die für eine Plattformversion implementiert wurden, funktionieren weiterhin, wenn die Plattform aktualisiert wird, und schützen so die Investitionen der Organisation in kundenspezifische Funktionen.

## Implementierung kundenspezifischer Dienste

Organisationen können kundenspezifische Dienste implementieren, die als vollwertige Komponenten in der Suite-Oberfläche erscheinen und nicht von nativen Funktionen zu unterscheiden sind.

**Controller-Implementierung**: Kundenspezifische Dienste implementieren eine Controller-Klasse, die vom Basis-Controller der Plattform erbt. Dieser Controller definiert die API-Endpunkte, Berechtigungsanforderungen und Metadaten des Dienstes. Die Implementierung folgt den Standard-FastAPI-Mustern, die Python-Entwicklern vertraut sind.

**Frontend-Komponentenentwicklung**: Dienste, die kundenspezifische Benutzeroberflächen benötigen, implementieren Frontend-Komponenten mit demselben Technologiestack wie die native Oberfläche – Nuxt 3, Vue 3 und PrimeVue. Diese Komponenten greifen über automatisch generierte TypeScript-Clients auf die API-Endpunkte des kundenspezifischen Controllers zu, wodurch die Typsicherheit über die Frontend-Backend-Grenze hinweg gewährleistet wird.

**Automatische Suite-Integration**: Wenn ein kundenspezifischer Controller bei der Plattform registriert wird, erscheint er automatisch in der dynamischen Dienstentdeckung der Suite. Benutzer mit den entsprechenden Berechtigungen sehen den kundenspezifischen Dienst in ihrer Seitenleisten-Navigation neben den nativen Diensten. Das Icon, der Name und die Beschreibung des kundenspezifischen Dienstes integrieren sich nahtlos in die einheitliche Oberfläche.

**Zugriff auf geteilte Infrastruktur**: Kundenspezifische Dienste erhalten automatisch Zugriff auf die Plattform-Infrastruktur – NATS-Messaging für ereignisgesteuerte Kommunikation, MongoDB-Persistenz für die Datenspeicherung, Authentifizierung/Autorisierung für die Sicherheit, Internationalisierung für mehrsprachige Unterstützung und Observability-Tools für Überwachung und Tracing.

## Anwendungsfälle für Erweiterungen

Organisationen implementieren verschiedene Arten von kundenspezifischen Diensten, um spezifische Geschäftsanforderungen zu erfüllen.

**Branchenspezifische Agents**: Eine Finanzdienstleistungsorganisation könnte kundenspezifische Agents für die Analyse der Einhaltung gesetzlicher Vorschriften, Finanzmodellierung oder Risikobewertung implementieren. Diese Agents integrieren sich in den Agent-Dienst der Suite und erscheinen neben nativen Agents mit branchenspezifischen Workflows und Wissensintegration.

**Integration proprietärer Systeme**: Organisationen können Dienste implementieren, die den AI Hub mit proprietären Unternehmenssystemen – ERP-Systemen, kundenspezifischen Datenbanken, Legacy-Anwendungen – verbinden. Diese Integrationsdienste könnten spezialisierte Agents bereitstellen, die mit proprietären Systemen interagieren, oder Überwachungsschnittstellen für KI-gesteuerte Automatisierung innerhalb dieser Systeme anbieten.

**Kundenspezifische Analyse-Dashboards**: Organisationen mit spezifischen Berichts- oder Analyseanforderungen können kundenspezifische Dashboard-Dienste implementieren, die Daten von Agents, Prozessen und Wissenssystemen aggregieren und organisationsspezifische Metriken und Visualisierungen präsentieren.

**Spezialisierte Workflows**: Prozessintensive Organisationen könnten kundenspezifische Prozessmanagement-Schnittstellen implementieren, die auf spezifische Workflow-Typen zugeschnitten sind – Dokumenten-Genehmigungs-Workflows, Compliance-Verifizierungsprozesse, mehrstufige Überprüfungsverfahren. Diese kundenspezifischen Schnittstellen nutzen die Prozessautomatisierungsinfrastruktur der Plattform und bieten gleichzeitig domänenspezifische Ansichten.

**Integration externer KI-Modelle**: Organisationen, die proprietäre oder spezialisierte KI-Modelle verwenden, können kundenspezifische Modellintegrationsdienste implementieren, die diese Modelle über die Suite verfügbar machen und es Agents ermöglichen, organisationsspezifische KI-Funktionen neben Standardmodellen zu nutzen.

## Entwicklungs-Workflow für Erweiterungen

Die Plattform bietet umfassende Tools und Dokumentationen zur Unterstützung der Entwicklung kundenspezifischer Dienste.

**Entwicklungsumgebung**: Organisationen richten lokale Entwicklungsumgebungen ein, die Produktionsbereitstellungen spiegeln, um die Entwicklung und das Testen kundenspezifischer Dienste ohne Beeinträchtigung der Produktionssysteme zu ermöglichen. Docker Compose-Konfigurationen stellen alle erforderliche Infrastruktur (Datenbanken, Message Buses, Observability-Tools) für die lokale Entwicklung bereit.

**Code-Generierung**: Die Plattform bietet Code-Generatoren, die neue Dienste mit korrekter Struktur, Boilerplate-Code und Integrationsmustern gerüsten. Entwickler beginnen mit funktionierenden Dienstvorlagen, anstatt von Grund auf neu zu entwickeln, was die Entwicklung beschleunigt und die Einhaltung der Plattformkonventionen sicherstellt.

**Testinfrastruktur**: Kundenspezifische Dienste nutzen dieselben Test-Frameworks wie native Dienste. Die Plattform bietet Test-Runner, die die Suite-Umgebung simulieren und so eine umfassende Prüfung kundenspezifischer Dienste vor der Bereitstellung ermöglichen.

**Dokumentationsvorlagen**: Die Plattform enthält Dokumentationsvorlagen und Beispiele, die die Implementierung kundenspezifischer Dienste, die Entwicklung von Frontend-Komponenten, das API-Design und die Suite-Integration demonstrieren. Diese Ressourcen beschleunigen die Entwicklung, indem sie funktionierende Beispiele gängiger Muster bereitstellen.

## Bereitstellung und Verteilung

Kundenspezifische Dienste werden zusammen mit der nativen Plattform bereitgestellt und werden zu integralen Bestandteilen der AI Hub-Installationen einer Organisation.

**Container-Verpackung**: Kundenspezifische Dienste werden als Docker-Container gemäß den Plattformkonventionen verpackt. Diese Container werden zusammen mit nativen Plattformkomponenten bereitgestellt, was eine unabhängige Skalierung und Versionsverwaltung ermöglicht.

**Konfigurationsmanagement**: Kundenspezifische Dienste verwenden das Konfigurationsmanagementsystem der Plattform und lesen Einstellungen aus Umgebungsvariablen und Konfigurationsdateien. Diese Integration ermöglicht konsistente Konfigurationspraktiken über native und kundenspezifische Dienste hinweg.

**Bereitstellungs-Orchestrierung**: Organisationen erweitern die Plattform-Bereitstellungskonfigurationen (Docker Compose-Dateien, Kubernetes-Manifeste), um kundenspezifische Dienste einzuschließen. Die Bereitstellungstools behandeln kundenspezifische Dienste identisch mit nativen Diensten und wenden dieselben Health Checks, Monitoring- und Lifecycle-Management-Verfahren an.

**Update-Unabhängigkeit**: Kundenspezifische Dienste können unabhängig von der nativen Plattform aktualisiert werden (innerhalb der Versionskompatibilitätsgarantien). Organisationen können neue Versionen kundenspezifischer Dienste bereitstellen, ohne vollständige Plattform-Updates zu benötigen, was eine agile Entwicklung kundenspezifischer Funktionen ermöglicht.

## Governance und Qualität

Obwohl die Plattform Erweiterbarkeit ermöglicht, behalten Organisationen die Kontrolle darüber, welche kundenspezifischen Dienste bereitgestellt werden und wie sie integriert werden.

**Berechtigungssteuerung**: Kundenspezifische Dienste deklarieren Berechtigungsanforderungen wie native Dienste. Administratoren steuern den Zugriff von Benutzern auf kundenspezifische Dienste über dieselben Rollen- und Berechtigungsverwaltungsoberflächen, die auch für native Funktionen verwendet werden.

**Qualitätsstandards**: Organisationen können Qualitätssicherungsmaßnahmen für die Bereitstellung kundenspezifischer Dienste festlegen – Anforderungen an die Codeüberprüfung, Teststandards, Sicherheitsaudits, Performance-Benchmarks. Die Erweiterbarkeit der Plattform schreibt keine niedrigeren Standards für kundenspezifische Dienste vor.

**Service-Registry**: Organisationen behalten über dieselben Überwachungs- und Verwaltungsoberflächen, die für native Dienste verwendet werden, den Überblick über bereitgestellte kundenspezifische Dienste. Kundenspezifische Dienste melden ihren Zustand, stellen Metriken bereit und generieren Audit-Logs identisch mit nativen Funktionen.

**Namespace-Isolation**: Organisationen können eine Namespace-Isolation implementieren, bei der kundenspezifische Dienste für verschiedene Organisationseinheiten sich nicht gegenseitig beeinflussen. Das Berechtigungssystem stellt angemessene Zugriffsgrenzen sicher.

## Potenzial für Community und Ökosystem

Die Erweiterbarkeitsarchitektur ermöglicht die potenzielle Entwicklung eines Ökosystems rund um die Swiss AI Hub Plattform.

**Geteilte Erweiterungen**: Organisationen könnten kundenspezifische Dienste mit Branchenkollegen teilen, die ähnliche Anforderungen haben. Ein kundenspezifischer Dienst für die Einhaltung gesetzlicher Vorschriften im Schweizer Bankwesen könnte mehreren Finanzinstituten zugutekommen und die kollaborative Entwicklung fördern.

**Partner-Ökosystem**: Technologiepartner könnten kundenspezifische Dienste entwickeln, die ihre Lösungen in den Swiss AI Hub integrieren und einen Marktplatz für komplementäre Funktionen schaffen, die Organisationen je nach ihren Bedürfnissen bereitstellen können.

**Innovationsbeschleunigung**: Durch die Ermöglichung der Entwicklung kundenspezifischer Dienste können Organisationen schnell auf neue Anforderungen reagieren, ohne auf native Plattformfunktionen warten zu müssen. Erfolgreiche kundenspezifische Dienste könnten die zukünftige Entwicklung nativer Plattformfunktionen beeinflussen.

**Wissensaustausch**: Die Community der Swiss AI Hub-Benutzer kann Implementierungsmuster, Best Practices und Referenzarchitekturen für gängige kundenspezifische Diensttypen austauschen und so die Fähigkeitsentwicklung des gesamten Ökosystems beschleunigen.

## Strategischer Wert für Organisationen

Die Erweiterbarkeit der Suite bietet Organisationen, die in KI-Fähigkeiten investieren, erhebliche strategische Vorteile.

**Zukunftssichere Investition**: Da sich die KI-Technologie weiterentwickelt und neue Funktionen entstehen, können Organisationen diese über kundenspezifische Dienste in ihre AI Hub-Bereitstellung integrieren. Die heutige Plattforminvestition bleibt relevant, wenn die Technologie fortschreitet.

**Vermeidung von Herstellerabhängigkeit**: Organisationen können proprietäre KI-Funktionen, kundenspezifische Modelle oder Drittanbieterdienste neben nativen Funktionen integrieren. Diese Flexibilität verhindert die Abhängigkeit von der Funktions-Roadmap oder den Technologieentscheidungen eines einzelnen Anbieters.

**Wettbewerbsdifferenzierung**: Organisationen können KI-Funktionen implementieren, die ihre einzigartigen Geschäftsprozesse, Branchenanforderungen oder Wettbewerbsstrategien widerspiegeln. Die Suite stellt die Infrastruktur bereit, während die Organisationen die Differenzierung kontrollieren.

**Inkrementelle Investition**: Anstatt massiver kundenspezifischer Entwicklungsprojekte können Organisationen fokussierte kundenspezifische Dienste implementieren, die spezifische Bedürfnisse adressieren, während sie native Funktionen für Standardanforderungen nutzen. Dies ermöglicht inkrementelle Investitionen, die auf die Wertschöpfung abgestimmt sind.

**Kontrolle über die Roadmap**: Organisationen bestimmen, welche kundenspezifischen Funktionen wann entwickelt werden, anstatt auf die Feature-Veröffentlichungen des Anbieters zu warten. Kritische Geschäftsanforderungen können durch kundenspezifische Entwicklung sofort adressiert werden.

## Technische Überlegungen

Organisationen, die kundenspezifische Dienste entwickeln möchten, sollten mehrere technische Faktoren berücksichtigen.

**Entwicklungsfähigkeiten**: Die Entwicklung kundenspezifischer Dienste erfordert Python-Kenntnisse für die Backend-Implementierung und TypeScript/Vue.js-Kenntnisse für die Frontend-Entwicklung. Organisationen sollten sicherstellen, dass sie Zugang zu Entwicklern mit diesen Fähigkeiten haben oder in Schulungen investieren.

**Wartungsaufwand**: Kundenspezifische Dienste erfordern eine kontinuierliche Wartung – Fehlerbehebungen, Sicherheitsupdates, Kompatibilität mit der Plattformentwicklung. Organisationen sollten eine langfristige Wartung planen, anstatt kundenspezifische Dienste als einmalige Entwicklungsprojekte zu betrachten.

**Testanforderungen**: Umfassende Tests sind für kundenspezifische Dienste unerlässlich, um sicherzustellen, dass sie die Stabilität oder Sicherheit der Plattform nicht beeinträchtigen. Organisationen sollten in Testinfrastruktur und -praktiken investieren, die für ihr Portfolio an kundenspezifischen Diensten geeignet sind.

**Dokumentation**: Kundenspezifische Dienste sollten nach denselben Standards wie native Funktionen dokumentiert werden, um sicherzustellen, dass Benutzer ihren Zweck, ihre Fähigkeiten und Nutzungsmuster verstehen. Dieser Dokumentationsaufwand sollte bei der Entwicklungsplanung berücksichtigt werden.

Diese Erweiterbarkeitsarchitektur stellt sicher, dass die Swiss AI Hub Suite eine Grundlage für die langfristige Entwicklung von KI-Fähigkeiten bietet. Sie ermöglicht es Organisationen, vertrauensvoll in die Plattform zu investieren, da sie wissen, dass sie diese an neue Anforderungen anpassen können, ohne das einheitliche Suite-Erlebnis zu beeinträchtigen oder Plattformmodifikationen zu erfordern, die Updates erschweren.
