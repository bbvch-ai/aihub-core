---
title: Erweiterbarkeit und Anpassung
source_sha: 0f7d9bdde6c962f5e867b612b897cdaa04d1d37ed846c01d18e093008bb45a78
---

# Erweiterbarkeit und Anpassung

Die Oberfläche der Swiss AI Hub Suite ist auf Erweiterbarkeit ausgelegt. Dies ermöglicht Organisationen,
benutzerdefinierte KI-Funktionen hinzuzufügen, proprietäre Systeme zu integrieren und die Plattform an spezifische
Geschäftsanforderungen anzupassen – und das alles bei Beibehaltung des einheitlichen Suite-Erlebnisses und ohne Änderung
des Kernplattform-Codes.

## Architektonische Grundlagen für Erweiterbarkeit

Die Erweiterbarkeit der Suite ergibt sich aus bewussten Architektur-Entscheidungen, die Erweiterungspunkte von der
Kerninfrastruktur trennen. Dies ermöglicht Organisationen, Funktionen hinzuzufügen, ohne die Codebasis zu forken oder
benutzerdefinierte Plattformversionen zu erstellen.

**Plugin-Architektur**: Dienste integrieren sich über ein gut definiertes Controller-Muster mit der Suite, anstatt durch
direkte Code-Integration. Organisationen, die benutzerdefinierte Dienste implementieren, folgen denselben Mustern wie
native Dienste, um sicherzustellen, dass ihre Erweiterungen automatisch in die Authentifizierungs-, Berechtigungs-,
Internationalisierungs- und Observability-Infrastruktur integriert werden.

**Standard-Integrationsverträge**: Das Controller-Muster definiert klare Verträge für die Dienstintegration.
Benutzerdefinierte Dienste implementieren diese Verträge, deklarieren ihre Metadaten (Name, Beschreibung, Icon,
Berechtigungen) und binden ihre API-Endpunkte ein. Die Suite erkennt und integriert konforme Controller automatisch,
ohne dass Änderungen an der Kernplattform erforderlich sind.

**Trennung von Kern und Erweiterung**: Die Plattform trennt explizit die Kerninfrastruktur (Authentifizierung,
Autorisierung, Messaging, Persistenz) von den Dienstimplementierungen. Erweiterungen nutzen die Kerninfrastruktur, ohne
sie zu modifizieren, wodurch sichergestellt wird, dass Plattform-Updates benutzerdefinierte Dienste nicht
beeinträchtigen und benutzerdefinierte Dienste die Stabilität der Kernplattform nicht gefährden.

**Versionskompatibilität**: Der Controller-Integrationsvertrag gewährleistet die Abwärtskompatibilität über
Plattformversionen hinweg. Dienste, die für eine Plattformversion implementiert wurden, funktionieren weiterhin, wenn
die Plattform aktualisiert wird, was die Investition der Organisation in benutzerdefinierte Funktionen schützt.

## Implementierung von benutzerdefinierten Diensten

Organisationen können benutzerdefinierte Dienste implementieren, die als „First-Class Citizens“ in der Suite-Oberfläche
erscheinen und von nativen Funktionen nicht zu unterscheiden sind.

**Controller-Implementierung**: Benutzerdefinierte Dienste implementieren eine Controller-Klasse, die vom
Basis-Controller der Plattform erbt. Dieser Controller definiert die API-Endpunkte, Berechtigungsanforderungen und
Metadaten des Dienstes. Die Implementierung folgt den standardmäßigen FastAPI-Mustern, die Python-Entwicklern vertraut
sind.

**Frontend-Komponentenentwicklung**: Dienste, die benutzerdefinierte Benutzeroberflächen benötigen, implementieren
Frontend-Komponenten mit demselben Technologie-Stack wie die native Oberfläche – Nuxt 3, Vue 3 und PrimeVue. Diese
Komponenten greifen über automatisch generierte TypeScript-Clients auf die API-Endpunkte des benutzerdefinierten
Controllers zu, wodurch die Typsicherheit über die Frontend-Backend-Grenze hinweg gewährleistet wird.

**Automatische Suite-Integration**: Wenn ein benutzerdefinierter Controller bei der Plattform registriert wird,
erscheint er automatisch in der dynamischen Dienst-Erkennung der Suite. Benutzer mit den entsprechenden Berechtigungen
sehen den benutzerdefinierten Dienst in ihrer Seitenleisten-Navigation neben den nativen Diensten. Das Icon, der Name
und die Beschreibung des benutzerdefinierten Dienstes integrieren sich nahtlos in die einheitliche Oberfläche.

**Zugriff auf gemeinsame Infrastruktur**: Benutzerdefinierte Dienste erhalten automatisch Zugriff auf die
Plattform-Infrastruktur – NATS Messaging für ereignisgesteuerte Kommunikation, MongoDB-Persistenz für die
Datenspeicherung, Authentifizierung/Autorisierung für die Sicherheit, Internationalisierung für mehrsprachige
Unterstützung und Observability-Tools für Überwachung und Nachverfolgung.

## Anwendungsfälle für Erweiterungen

Organisationen implementieren verschiedene Arten von benutzerdefinierten Diensten, um spezifische Geschäftsanforderungen
zu erfüllen.

**Branchenspezifische Agenten**: Eine Finanzdienstleistungsorganisation könnte benutzerdefinierte Agenten für die
Analyse der Einhaltung gesetzlicher Vorschriften, Finanzmodellierung oder Risikobewertung implementieren. Diese Agenten
integrieren sich in den Agenten-Dienst der Suite und erscheinen neben nativen Agenten mit branchenspezifischen Workflows
und Wissensintegration.

**Integration proprietärer Systeme**: Organisationen können Dienste implementieren, die den AI Hub mit proprietären
Unternehmenssystemen – ERP-Systemen, benutzerdefinierten Datenbanken, Legacy-Anwendungen – verbinden. Diese
Integrationsdienste könnten spezialisierte Agenten bereitstellen, die mit proprietären Systemen interagieren, oder
Überwachungsschnittstellen für KI-gesteuerte Automatisierung innerhalb dieser Systeme anbieten.

**Benutzerdefinierte Analyse-Dashboards**: Organisationen mit spezifischen Berichts- oder Analyseanforderungen können
benutzerdefinierte Dashboard-Dienste implementieren, die Daten von Agenten, Prozessen und Wissenssystemen aggregieren
und organisationsspezifische Metriken und Visualisierungen präsentieren.

**Spezialisierte Workflows**: Prozessintensive Organisationen könnten benutzerdefinierte Prozessmanagement-Oberflächen
implementieren, die auf spezifische Workflow-Typen zugeschnitten sind – Dokumentengenehmigungs-Workflows,
Compliance-Verifizierungsprozesse, mehrstufige Überprüfungsverfahren. Diese benutzerdefinierten Oberflächen nutzen die
Prozessautomatisierungs-Infrastruktur der Plattform, präsentieren aber domänenspezifische Ansichten.

**Integration externer KI-Modelle**: Organisationen, die proprietäre oder spezialisierte KI-Modelle verwenden, können
benutzerdefinierte Modellintegrationsdienste implementieren, die diese Modelle über die Suite verfügbar machen, sodass
Agenten neben Standardmodellen auch organisationsspezifische KI-Funktionen nutzen können.

## Workflow für die Erweiterungsentwicklung

Die Plattform bietet umfassende Tools und Dokumentationen zur Unterstützung der Entwicklung benutzerdefinierter Dienste.

**Entwicklungsumgebung**: Organisationen richten lokale Entwicklungsumgebungen ein, die Produktions-Deployments
widerspiegeln, was die Entwicklung und das Testen benutzerdefinierter Dienste ermöglicht, ohne Produktionssysteme zu
beeinträchtigen. Docker Compose-Konfigurationen stellen die gesamte erforderliche Infrastruktur (Datenbanken, Message
Buses, Observability-Tools) für die lokale Entwicklung bereit.

**Codegenerierung**: Die Plattform bietet Codegeneratoren, die neue Dienste mit korrekter Struktur, Boilerplate-Code und
Integrationsmustern ausstatten. Entwickler beginnen mit funktionierenden Dienstvorlagen, anstatt von Grund auf neu zu
entwickeln, was die Entwicklung beschleunigt und die Einhaltung der Plattformkonventionen sicherstellt.

**Testinfrastruktur**: Benutzerdefinierte Dienste nutzen dieselben Test-Frameworks wie native Dienste. Die Plattform
stellt Test-Runner bereit, die die Suite-Umgebung simulieren und umfassende Tests benutzerdefinierter Dienste vor der
Bereitstellung ermöglichen.

**Dokumentationsvorlagen**: Die Plattform enthält Dokumentationsvorlagen und Beispiele, die die Implementierung
benutzerdefinierter Dienste, die Entwicklung von Frontend-Komponenten, das API-Design und die Suite-Integration
demonstrieren. Diese Ressourcen beschleunigen die Entwicklung, indem sie funktionierende Beispiele gängiger Muster
bereitstellen.

## Bereitstellung und Verteilung

Benutzerdefinierte Dienste werden zusammen mit der nativen Plattform bereitgestellt und werden zu integralen
Bestandteilen der AI Hub-Installationen einer Organisation.

**Container-Verpackung**: Benutzerdefinierte Dienste werden als Docker-Container gemäß den Plattformkonventionen
verpackt. Diese Container werden zusammen mit den nativen Plattformkomponenten bereitgestellt, was eine unabhängige
Skalierung und Versionsverwaltung ermöglicht.

**Konfigurationsmanagement**: Benutzerdefinierte Dienste verwenden das Konfigurationsmanagementsystem der Plattform und
lesen Einstellungen aus Umgebungsvariablen und Konfigurationsdateien. Diese Integration ermöglicht konsistente
Konfigurationspraktiken über native und benutzerdefinierte Dienste hinweg.

**Bereitstellungs-Orchestrierung**: Organisationen erweitern die Plattform-Bereitstellungskonfigurationen (Docker
Compose-Dateien, Kubernetes-Manifeste), um benutzerdefinierte Dienste einzuschließen. Bereitstellungstools behandeln
benutzerdefinierte Dienste identisch mit nativen Diensten und wenden dieselben Health Checks, Überwachungen und das
Lifecycle-Management an.

**Update-Unabhängigkeit**: Benutzerdefinierte Dienste können unabhängig von der nativen Plattform aktualisiert werden
(innerhalb der Versionskompatibilitätsgarantien). Organisationen können neue Versionen benutzerdefinierter Dienste
bereitstellen, ohne vollständige Plattform-Updates zu erfordern, was eine agile Entwicklung benutzerdefinierter
Funktionen ermöglicht.

## Governance und Qualität

Während die Plattform Erweiterbarkeit ermöglicht, behalten Organisationen die Kontrolle darüber, welche
benutzerdefinierten Dienste bereitgestellt und wie sie integriert werden.

**Berechtigungssteuerung**: Benutzerdefinierte Dienste deklarieren Berechtigungsanforderungen wie native Dienste.
Administratoren steuern den Zugriff von Benutzern auf benutzerdefinierte Dienste über dieselben Rollen- und
Berechtigungsmanagement-Oberflächen, die für native Funktionen verwendet werden.

**Qualitätsstandards**: Organisationen können Qualitäts-Gates für die Bereitstellung benutzerdefinierter Dienste
festlegen – Code-Review-Anforderungen, Teststandards, Sicherheitsaudits, Performance-Benchmarks. Die Erweiterbarkeit der
Plattform erzwingt keine niedrigeren Standards für benutzerdefinierte Dienste.

**Diensteregister**: Organisationen behalten durch dieselben Überwachungs- und Verwaltungsoberflächen, die für native
Dienste verwendet werden, den Überblick über bereitgestellte benutzerdefinierte Dienste. Benutzerdefinierte Dienste
melden den Zustand, geben Metriken aus und generieren Audit-Logs identisch mit nativen Funktionen.

**Namespace-Isolation**: Organisationen können eine Namespace-Isolation implementieren, bei der benutzerdefinierte
Dienste für verschiedene Organisationseinheiten sich nicht gegenseitig beeinflussen. Das Berechtigungssystem
gewährleistet angemessene Zugriffsbarrieren.

## Potenzial für Community und Ökosystem

Die Erweiterungsarchitektur ermöglicht die potenzielle Entwicklung eines Ökosystems rund um die Swiss AI Hub Plattform.

**Geteilte Erweiterungen**: Organisationen könnten benutzerdefinierte Dienste mit Branchenkollegen teilen, die ähnliche
Anforderungen haben. Ein benutzerdefinierter Dienst für die Einhaltung gesetzlicher Vorschriften im Schweizer Bankwesen
könnte mehreren Finanzinstituten zugutekommen und die Zusammenarbeit fördern.

**Partner-Ökosystem**: Technologiepartner könnten benutzerdefinierte Dienste entwickeln, die ihre Lösungen in den Swiss
AI Hub integrieren und einen Marktplatz komplementärer Funktionen schaffen, die Organisationen je nach ihren
Bedürfnissen bereitstellen können.

**Innovationsbeschleunigung**: Durch die Ermöglichung der Entwicklung benutzerdefinierter Dienste können Organisationen
schnell auf neue Anforderungen reagieren, ohne auf native Plattformfunktionen warten zu müssen. Erfolgreiche
benutzerdefinierte Dienste könnten die zukünftige native Plattformentwicklung beeinflussen.

**Wissensaustausch**: Die Community der Swiss AI Hub-Benutzer kann Implementierungsmuster, Best Practices und
Referenzarchitekturen für gängige benutzerdefinierte Diensttypen austauschen, was die Fähigkeitsentwicklung des gesamten
Ökosystems beschleunigt.

## Strategischer Wert für Organisationen

Die Erweiterbarkeit der Suite bietet Organisationen, die in KI-Funktionen investieren, erhebliche strategische Vorteile.

**Zukunftssichere Investition**: Wenn sich die KI-Technologie weiterentwickelt und neue Funktionen entstehen, können
Organisationen diese über benutzerdefinierte Dienste in ihre AI Hub-Bereitstellung integrieren. Die heutige
Plattforminvestition bleibt relevant, während die Technologie fortschreitet.

**Vermeidung von Herstellerbindung**: Organisationen können proprietäre KI-Funktionen, benutzerdefinierte Modelle oder
Dienste von Drittanbietern neben nativen Funktionen integrieren. Diese Flexibilität verhindert die Abhängigkeit von der
Feature-Roadmap oder den Technologieentscheidungen eines einzelnen Anbieters.

**Wettbewerbsdifferenzierung**: Organisationen können KI-Funktionen implementieren, die ihre einzigartigen
Geschäftsprozesse, Branchenanforderungen oder Wettbewerbsstrategien widerspiegeln. Die Suite bietet Infrastruktur,
während Organisationen die Differenzierung kontrollieren.

**Inkrementelle Investition**: Anstatt massiver kundenspezifischer Entwicklungsprojekte können Organisationen
fokussierte benutzerdefinierte Dienste implementieren, die spezifische Anforderungen adressieren, während sie für
Standardanforderungen native Funktionen nutzen. Dies ermöglicht inkrementelle Investitionen, die auf die Wertschöpfung
ausgerichtet sind.

**Kontrolle über die Roadmap**: Organisationen bestimmen, welche benutzerdefinierten Funktionen wann entwickelt werden
sollen, anstatt auf Feature-Veröffentlichungen des Anbieters zu warten. Kritische Geschäftsanforderungen können durch
benutzerdefinierte Entwicklung sofort adressiert werden.

## Technische Überlegungen

Organisationen, die die Entwicklung benutzerdefinierter Dienste planen, sollten mehrere technische Faktoren
berücksichtigen.

**Entwicklungsfähigkeiten**: Die Entwicklung benutzerdefinierter Dienste erfordert Python-Kenntnisse für die
Backend-Implementierung und TypeScript/Vue.js-Kenntnisse für die Frontend-Entwicklung. Organisationen sollten
sicherstellen, dass sie Zugang zu Entwicklern mit diesen Fähigkeiten haben oder in Schulungen investieren.

**Wartungsaufwand**: Benutzerdefinierte Dienste erfordern laufende Wartung – Fehlerbehebungen, Sicherheitsupdates,
Kompatibilität mit der Plattformentwicklung. Organisationen sollten eine langfristige Wartung planen, anstatt
benutzerdefinierte Dienste als einmalige Entwicklungsprojekte zu betrachten.

**Testanforderungen**: Umfassende Tests sind für benutzerdefinierte Dienste unerlässlich, um sicherzustellen, dass sie
die Plattformstabilität oder -sicherheit nicht gefährden. Organisationen sollten in eine Testinfrastruktur und
-praktiken investieren, die für ihr Portfolio an benutzerdefinierten Diensten geeignet sind.

**Dokumentation**: Benutzerdefinierte Dienste sollten nach denselben Standards wie native Funktionen dokumentiert
werden, um sicherzustellen, dass Benutzer ihren Zweck, ihre Funktionen und Nutzungsmuster verstehen. Dieser
Dokumentationsaufwand sollte in die Entwicklungsplanung einfließen.

Diese Erweiterungsarchitektur stellt sicher, dass die Swiss AI Hub Suite eine Grundlage für die langfristige Entwicklung
von KI-Funktionen bietet. Sie ermöglicht es Organisationen, selbstbewusst in die Plattform zu investieren, da sie
wissen, dass sie diese an neue Anforderungen anpassen können, ohne das einheitliche Suite-Erlebnis zu beeinträchtigen
oder Plattformmodifikationen zu erfordern, die Updates erschweren.
