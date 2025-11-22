# Kapitel 16: Erweiterbarkeit und Zukunftssicherheit

Die Investition in Künstliche Intelligenz (KI) erfordert für Schweizer Unternehmen mehr als nur die Wahl einer
leistungsstarken Technologie; sie verlangt eine strategische Entscheidung für eine Plattform, die langfristige
Stabilität, Anpassungsfähigkeit und technologische Unabhängigkeit gewährleistet. In einem sich rasant entwickelnden
KI-Ökosystem ist die Fähigkeit, neue Technologien nahtlos zu integrieren und bestehende Lösungen flexibel zu erweitern,
entscheidend, um Wettbewerbsvorteile zu sichern und hohe Refactoring-Kosten zu vermeiden. Dieses Kapitel legt dar, wie
der Swiss AI Hub durch seine offene und modulare Architektur diese Anforderungen erfüllt und Unternehmen eine
zukunftssichere und souveräne KI-Basis bietet.

## 1. Souveränität durch Open Source und Herstellerunabhängigkeit

### Mehrwert und Nutzen: Langfristige Investitionssicherheit und vollständige Kontrolle

Für C-Level-Führungskräfte ist die Vermeidung von Vendor Lock-in ein strategischer Imperativ, um langfristige
Kostenkontrolle und Handlungsfähigkeit zu sichern. Eine Open-Source-Plattform bietet hier die Gewissheit, dass die
Investition in die KI-Infrastruktur dauerhaft geschützt ist und sich flexibel an zukünftige Marktbedingungen anpassen
lässt. IT-Verantwortliche profitieren von der Möglichkeit, den Code zu inspizieren, zu modifizieren und die Software
auch bei einem hypothetischen Ausfall des ursprünglichen Anbieters autonom weiterzubetreiben. Dies schafft maximale
Transparenz und Auditierbarkeit, was wiederum die Einhaltung strenger Schweizer Datenschutz- und
Compliance-Anforderungen erleichtert. Es fallen keine Lizenzgebühren an, lediglich die Kosten für die Infrastruktur, auf
der die Plattform betrieben wird.

### Konzepte & Prozesse: Open-Source-Lizenz und modulare Systemarchitektur

Der Swiss AI Hub ist unter der Apache 2.0 Lizenz veröffentlicht. Dieses Open-Source-Modell eliminiert das Risiko des
Vendor Lock-in vollständig, da der Code den Organisationen gehört, überall ausgeführt und bei Bedarf modifiziert oder
geforkt werden kann. Die Plattform ist zudem bewusst modular aufgebaut. Dies bedeutet, dass kritische Komponenten wie
Datenbanken, Vektor-Stores und LLM-Provider flexibel ausgetauscht werden können. Diese Architektur unterstützt hybride
Modelle, die den Einsatz von kommerziellen Cloud-Modellen, lokal gehosteten Open-Source-LLMs oder einer Kombination
davon ermöglichen und so die strategische Unabhängigkeit von einem einzelnen AI-Provider gewährleisten. Die Basis auf
offenen Standards gewährleistet zudem, dass Daten jederzeit exportierbar sind und keine proprietären Formate Lock-in
erzeugen.

### Technische Umsetzung im Swiss AI Hub: LiteLLM und austauschbare Komponenten

Technisch basiert der Swiss AI Hub auf einem vereinheitlichten **LLM-Proxy (LiteLLM)**, der eine OpenAI-kompatible API
bereitstellt und anbieterspezifische APIs abstrahiert. Dies ermöglicht den nahtlosen Wechsel zwischen Modellen von
Anbietern wie Azure OpenAI, Google Gemini oder selbst gehosteten Modellen (z.B. über vLLM, llama.cpp, HF-TEI) ohne
Codeänderungen. Der LiteLLM-Proxy ist pro Instanz konfiguriert und verwaltet Modell-Auswahl, Budgets und
Ratenbegrenzungen. Die Plattform unterstützt den **Air-Gapped-Betrieb** mit lokalen LLMs. Daten werden in offenen
Formaten in Komponenten wie **FerretDB/PostgreSQL** (für Datenbanken), **Milvus** (für Vektor-Stores) und **SeaweedFS**
(für Dokumentenspeicherung) gespeichert, wodurch proprietäre Formate vermieden und die Datenportabilität garantiert
wird. Die Architektur ermöglicht es, einzelne Komponenten bei Bedarf auszutauschen oder den zugrundeliegenden Code (z.B.
durch Forking) zu modifizieren.

## 2. Individuelle Erweiterbarkeit und Integration in bestehende IT-Landschaften

### Mehrwert und Nutzen: Massgeschneiderte Lösungen und maximaler Investitionsschutz

Für Führungskräfte ermöglicht die individuelle Erweiterbarkeit der Plattform die Entwicklung massgeschneiderter
KI-Lösungen, die exakt auf spezifische Geschäftsanforderungen und -prozesse zugeschnitten sind. Dies steigert die
Wettbewerbsfähigkeit und den ROI, da die KI dort zum Einsatz kommt, wo sie den grössten Wert schafft. IT-Teams
profitieren von umfassenden APIs und SDKs, die eine reibungslose Integration in bestehende ERP-, CRM- oder
Fachanwendungen ermöglichen. Dies schützt Investitionen in vorhandene IT-Systeme und reduziert den Aufwand für die
Entwicklung von Insellösungen, da Custom-Integrationen und -Workflows effizient entwickelt werden können.

### Konzepte & Prozesse: Plugin-Architektur und API-First-Ansatz

Der Swiss AI Hub ist auf Erweiterbarkeit ausgelegt und verfolgt einen konsequenten API-First-Ansatz. Die
**Plugin-Architektur** ermöglicht es Organisationen, benutzerdefinierte Dienste als "First-Class Citizens" zu
implementieren. Diese erweiterten Dienste folgen denselben Mustern wie native Komponenten und integrieren sich
automatisch in die Authentifizierungs-, Berechtigungs-, Internationalisierungs- und Observability-Infrastruktur der
Plattform. Das **AI-Hub SDK** stellt die nötigen Werkzeuge bereit, um spezialisierte Agenten, Pipelines und Workflows zu
entwickeln, die sich nahtlos in die bestehende Infrastruktur integrieren. Dies fördert die Zusammenarbeit der Community,
die Erweiterungen beitragen kann.

### Technische Umsetzung im Swiss AI Hub: SDK, APIs und Custom Services

Das **AI-Hub SDK** ermöglicht die Entwicklung von benutzerdefinierten Agenten und Pipelines mit klaren Schnittstellen.
Organisationen können Controller-Klassen implementieren, die vom Basis-Controller der Plattform erben, API-Endpunkte
definieren und Metadaten (Name, Icon, Berechtigungen) deklarieren. Diese benutzerdefinierten Dienste erscheinen
automatisch in der dynamischen Dienst-Erkennung der Suite und erhalten Zugriff auf die gemeinsame Infrastruktur (NATS
Messaging, MongoDB-Persistenz, Authentifizierung/Autorisierung, Internationalisierung, Observability). Die Plattform
stellt zudem eine **OpenAI-kompatible REST-API** für die Migration bestehender KI-Anwendungen bereit sowie eine
**Agenten-Interaktions-REST-API** für programmatischen Zugriff auf Plattformfunktionen. Eine **WebSocket-API** dient der
Echtzeit-Kommunikation. Frontend-Komponenten können mit Nuxt 3, Vue 3 und PrimeVue entwickelt werden. Der **Model
Context Protocol (MCP) Server** ermöglicht die Integration in externe KI-Entwicklungsassistenten.

## 3. Zukunftssichere Technologiebasis und nachhaltiges Lifecycle-Management

### Mehrwert und Nutzen: Langfristige Relevanz und stabile Betriebskontinuität

Eine zukunftssichere Technologiebasis ist für C-Level-Führungskräfte entscheidend, um sicherzustellen, dass heutige
KI-Investitionen auch morgen noch relevant sind und sich flexibel an neue technologische Trends anpassen lassen. Eine
transparente Roadmap und professionelle Support-Strukturen gewährleisten die Betriebskontinuität und minimieren Risiken
durch veraltete Software. IT-Teams profitieren von einer Plattform, die auf Cloud-native-Prinzipien und offene Standards
setzt, was die Skalierbarkeit, Wartbarkeit und automatisierte Bereitstellung erheblich vereinfacht und
Zero-Downtime-Updates sowie effektive Rollbacks ermöglicht.

### Konzepte & Prozesse: Cloud-native, Versionierung und unterbrechungsfreie Updates

Der Swiss AI Hub ist konsequent auf **Cloud-native-Prinzipien** und offene Industriestandards (z.B. OpenTelemetry)
ausgerichtet, um in modernen Infrastrukturen skalierbar zu bleiben. Die Plattform und kundenspezifische Erweiterungen
nutzen **semantische Versionierung** und können unabhängig voneinander aktualisiert werden. Dies ermöglicht einen
kontrollierten Rollout-Prozess und die Sicherstellung der Abwärtskompatibilität für Minor- und Patch-Releases. Für
Major-Updates mit Breaking Changes ist ein koordinierter Ansatz erforderlich, bei dem Kern- und Kundencode gemeinsam
aktualisiert werden. Strategien für **Zero-Downtime-Updates** durch inkrementelle Rollouts sind vorgesehen, und
**Rollback-Fähigkeiten** über VM-Snapshots oder Versions-Tags sichern schnelle Fehlerbehebungen.

### Technische Umsetzung im Swiss AI Hub: Docker, Kubernetes-Readiness und Support-Strukturen

Die Plattform ist containerisiert (Docker) und damit prinzipiell **Kubernetes-ready**, was eine hochskalierbare und
automatisierte Bereitstellung in modernen Cloud-Umgebungen ermöglicht. Das `docker compose up`-Kommando startet eine
vollständige Instanz. Updates der Core-Plattform (API, Web, Dagster) und des kundenspezifischen Codes (Agenten,
Pipelines) können durch Aktualisierung der Docker-Image-Tags und Neustart der Services erfolgen. Bei Problemen erlauben
**VM-Snapshots** oder das Zurücksetzen auf vorherige Image-Tags einen schnellen Rollback. Die **bbv als
Plattformanbieter bietet professionelle Support- und Schulungsangebote**, um Organisationen bei der Implementierung, dem
Betrieb und der Weiterentwicklung zu unterstützen. Die Roadmap wird aktiv gepflegt, und neue Features werden unter
Beachtung der Abwärtskompatibilität eingeführt. Die Kompatibilität zwischen Kunden- und Core-Versionen wird durch eine
Kompatibilitätsmatrix verfolgt.
