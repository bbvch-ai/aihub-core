# Kapitel 16: Erweiterbarkeit und Zukunftssicherheit

Die technologische Halbwertszeit im Bereich der künstlichen Intelligenz ist extrem kurz. Modelle, die heute als
Marktführer gelten, können morgen bereits veraltet sein. Für Unternehmen stellt dies ein erhebliches Investitionsrisiko
dar, da sich die Frage stellt, wie man eine langfristige Infrastruktur auf einem Fundament baut, das sich ständig
bewegt. Eine starre Plattform, die eng an einen spezifischen Anbieter oder eine momentane Technologiegeneration
gekoppelt ist, wird schnell zur technischen Schuld.

Der Swiss AI Hub begegnet dieser Dynamik mit einer Architektur, die radikal auf Wandelbarkeit ausgelegt ist. Dieses
Kapitel beschreibt, wie die Plattform durch Modularität, offene Standards und eine strikte Trennung von Kernsystem und
Kundenlogik sicherstellt, dass Ihre Investition auch in Jahren noch werthaltig ist. Es wird aufgezeigt, wie Sie eigene
Innovationen nahtlos in die Suite integrieren, ohne die Update-Fähigkeit des Gesamtsystems zu gefährden.

## Auf einen Blick

- **Lizenzrechtliche Unabhängigkeit:** Die Veröffentlichung unter der Apache 2.0 Lizenz garantiert, dass der Quellcode
  dauerhaft prüfbar, anpassbar und frei von Lizenzgebühren bleibt.
- **Vermeidung von Vendor-Lock-in:** Ein modulares LLM-Gateway ermöglicht den Austausch von Modell-Anbietern,
  beispielsweise von Azure zu Google oder lokalen Modellen, rein durch Konfiguration.
- **Native Erweiterbarkeit:** Das «Controller-Pattern» erlaubt Entwicklern, eigene Dienste zu bauen, die automatisch
  erkannt und nahtlos in die Benutzeroberfläche und Infrastruktur integriert werden.
- **Automatisierte API-Generierung:** Das System erstellt on-the-fly typensichere REST-Endpunkte für jeden neuen
  Agenten, was manuelle Entwicklungsengpässe eliminiert.
- **Sicheres Lifecycle-Management:** Durch «Version Pinning» in der Projektkonfiguration bleiben kundenspezifische
  Erweiterungen stabil, auch wenn die Kernplattform aktualisiert wird.

## Investitionsschutz durch Open Source und Standards

### Geschäftlicher Nutzen

Ein klassisches Risiko bei der Beschaffung von Enterprise-Software ist der «Vendor Lock-in». Kunden geraten in eine
Abhängigkeit, in der sie Preiserhöhungen, Lizenzänderungen oder Strategiewechsel des Herstellers ausgeliefert sind. Im
schlimmsten Fall stellt ein Anbieter den Betrieb ein, und das darauf aufgebaute Unternehmenswissen geht verloren. CIOs
und Einkäufer fordern daher Garantien für langfristige Verfügbarkeit und Unabhängigkeit. Eine Plattform muss
sicherstellen, dass das Unternehmen jederzeit Eigentümer seiner Architektur und Daten bleibt, unabhängig von externen
Marktkräften.

### Konzeptioneller Ansatz

Der Swiss AI Hub basiert auf der Philosophie der technologischen Souveränität. Dies wird primär durch die
Veröffentlichung unter der Apache 2.0 Lizenz gewährleistet. Diese liberale Open-Source-Lizenz garantiert, dass der
Quellcode der Plattform für den Mandanten einsehbar, modifizierbar und dauerhaft nutzbar ist. Ergänzend dazu setzt die
Architektur konsequent auf offene Industriestandards statt auf proprietäre Formate. Dies betrifft Schnittstellen,
Datenhaltung und Kommunikationsprotokolle, was eine nahtlose Portabilität und Interoperabilität gewährleistet.

### Technische Umsetzung im Swiss AI Hub

Die technische Basis bildet ein Stack aus bewährten Open-Source-Komponenten, die keine «Black Boxes» darstellen. Da der
Kerncode offenliegt, können interne Sicherheitsteams die Integrität der Software jederzeit verifizieren. Es werden keine
proprietären Speicherformate verwendet. Vektordaten residieren in Milvus, relationale Daten in PostgreSQL und Dateien in
S3-kompatiblen Objektspeichern wie SeaweedFS. Ein Export der Daten ist durch Standard-Datenbank-Tools jederzeit möglich.
Durch die Unterstützung des «Model Context Protocol» (MCP) öffnet sich die Plattform zudem für externe KI-Assistenten
und Entwicklungsumgebungen, die den Plattformstatus über standardisierte Endpunkte inspizieren können.

## Modulare Architektur und Vermeidung von Modell-Lock-in

### Geschäftlicher Nutzen

Der Markt für Large Language Models (LLMs) ist volatil. Während heute vielleicht ein bestimmtes Modell führt, könnten
morgen spezialisierte Open-Source-Modelle das beste Preis-Leistungs-Verhältnis bieten. Eine Anwendung, deren Code fest
auf die API eines einzelnen Anbieters zugeschnitten ist, erfordert bei jedem Wechsel ein teures Refactoring. Unternehmen
benötigen eine Infrastruktur, die «modell-agnostisch» ist und es erlaubt, die Intelligenz im Hintergrund auszutauschen,
ohne die Geschäftsprozesse im Vordergrund zu stören oder Sicherheitsrichtlinien neu definieren zu müssen.

### Konzeptioneller Ansatz

Die Plattform verfolgt das Prinzip der losen Kopplung. Kritische Komponenten, insbesondere das Sprachmodell, die
Vektordatenbank und der Embeddings-Provider, werden als austauschbare Module betrachtet. Eine Abstraktionsschicht
entkoppelt die Anwendungslogik von der spezifischen Implementierung. Dies erlaubt Administratoren, Komponenten durch
Konfiguration statt durch Programmierung zu wechseln. Das System ist somit «Batteries Included, but Swappable», was
bedeutet, dass es mit funktionierenden Standardkomponenten geliefert wird, aber den Kunden nicht zwingt, diese dauerhaft
zu nutzen.

### Technische Umsetzung im Swiss AI Hub

Zentrales Element für diese Flexibilität ist das LLM-Gateway, welches durch LiteLLM implementiert wird. Dieses Gateway
normalisiert die APIs von über 100 Anbietern. Ein Wechsel von Azure OpenAI zu Google Gemini oder zu einem lokalen Modell
via vLLM oder llama.cpp erfordert lediglich eine Anpassung der YAML-Konfiguration in der «model_list». Die Logik der
AI-Agenten bleibt davon unberührt, da sie gegen eine vereinheitlichte Schnittstelle programmiert ist. Zudem erlaubt die
Konfiguration komplexes Routing, um Lasten auf verschiedene Modelle zu verteilen oder Fallbacks zu definieren, falls ein
Anbieter nicht erreichbar ist.

## Erweiterbarkeit durch SDK und Plugin-System

### Geschäftlicher Nutzen

Kein Standardprodukt kann die spezifischen Anforderungen jedes Unternehmens zu 100 Prozent abdecken. Oft scheitern
Plattformen daran, dass Anpassungen den Kerncode verändern, was zukünftige Updates unmöglich macht oder extrem
verteuert. Die Anforderung lautet daher, maximale Anpassbarkeit bei gleichzeitiger Wahrung der Update-Fähigkeit des
Kernsystems sicherzustellen. Unternehmen müssen in der Lage sein, eigene Geschäftslogik als Erweiterung zu bauen, die
sich nahtlos in die Suite einfügt und automatisch von allen Plattformfunktionen profitiert.

### Konzeptioneller Ansatz

Der Swiss AI Hub bietet ein Software Development Kit (SDK) und eine Plugin-Architektur, die Erweiterungen als
gleichberechtigte Bestandteile behandelt. Das Architekturmuster trennt strikt zwischen der Kerninfrastruktur, die durch
die Plattform bereitgestellt wird, und benutzerdefinierten Diensten, welche durch den Kunden entwickelt werden. Das SDK
eliminiert Redundanz, da die Plattform bereits das Streaming, die Authentifizierung und das Tracing übernimmt. Erstellt
ein Entwickler einen neuen Agenten-Bauplan, erbt dieser automatisch alle Enterprise-Fähigkeiten der Plattform.

### Technische Umsetzung im Swiss AI Hub

Die Erweiterbarkeit wird durch das «Controller-Pattern» realisiert. Benutzerdefinierte Dienste erben von einer
Basis-Controller-Klasse und definieren dort ihre Metadaten und API-Endpunkte. Die Plattform erkennt diese Dienste beim
Start automatisch über eine «Service Discovery» und integriert sie dynamisch in die Benutzeroberfläche. Ein
technologischer Meilenstein sind die dynamischen Endpunkte, bei denen der «AgentEndpointsDiscoveryService» automatisch
REST-Schnittstellen für neue Agenten generiert. Da Erweiterungen denselben Technologie-Stack mit Nuxt 3 und Vue 3
nutzen, fügen sie sich nahtlos in das Erscheinungsbild der Suite ein, während sie gleichzeitig Zugriff auf die
gemeinsame Infrastruktur wie NATS oder MongoDB erhalten.

## Lifecycle-Management und Update-Strategie

### Geschäftlicher Nutzen

Software altert, und ohne regelmässige Updates entstehen Sicherheitslücken. Die Angst vor inkompatiblen Änderungen führt
jedoch oft dazu, dass Systeme veralten. Unternehmen benötigen eine Update-Strategie, die Stabilität garantiert. Es muss
möglich sein, die zugrundeliegende Plattform zu aktualisieren, um von Sicherheits-Patches und neuen Features zu
profitieren, ohne dass mühsam entwickelte, kundenspezifische Agenten-Profile und Workflows funktionsunfähig werden.

### Konzeptioneller Ansatz

Der Swiss AI Hub löst dieses Problem durch eine strikte Trennung von Core-Plattform und Custom-Code in Kombination mit
semantischer Versionierung. Die Plattform entwickelt sich unabhängig von der Kundenanwendung weiter. Die Kundenanwendung
deklariert explizit, mit welcher Version des Cores sie kompatibel ist. Dies verhindert, dass ein automatisches
Plattform-Update ungewollt Inkompatibilitäten einführt, da Updates bewusst und kontrolliert durchgeführt werden können.

### Technische Umsetzung im Swiss AI Hub

Das technische Management erfolgt über Docker-Container und die Python-Paketverwaltung. In der Konfiguration des
Kundenprojekts, beispielsweise in der «pyproject.toml», wird die Abhängigkeit zum Core fixiert. Ein Update des Cores
erfordert eine aktive Änderung dieser Version, was Raum für Tests in einer Staging-Umgebung schafft. Da Core-Dienste und
Kunden-Dienste in separaten Containern laufen, können sie unabhängig voneinander skaliert und aktualisiert werden. Die
Unterstützung von Rolling Updates ermöglicht es zudem, neue Versionen bereitzustellen, ohne den laufenden Betrieb zu
unterbrechen, während unveränderliche Docker-Images eine einfache Rollback-Fähigkeit bei Problemen sicherstellen.
