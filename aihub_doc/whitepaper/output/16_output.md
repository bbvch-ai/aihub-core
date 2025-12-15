# Kapitel 16: Erweiterbarkeit und Zukunftssicherheit

Die technologische Halbwertszeit im Bereich der künstlichen Intelligenz ist extrem kurz. Modelle, die heute als
Marktführer gelten, können morgen bereits veraltet sein. Für Unternehmen stellt dies ein erhebliches Investitionsrisiko
dar: Wie baut man eine langfristige Infrastruktur auf einem Fundament, das sich ständig bewegt? Eine starre Plattform,
die eng an einen spezifischen Anbieter oder eine momentane Technologiegeneration gekoppelt ist, wird schnell zur
technischen Schuld.

Der Swiss AI Hub begegnet dieser Dynamik mit einer Architektur, die radikal auf Wandelbarkeit ausgelegt ist. Dieses
Kapitel beschreibt, wie die Plattform durch Modularität, offene Standards und eine strikte Trennung von Kernsystem und
Kundenlogik sicherstellt, dass Ihre Investition auch in fünf Jahren noch werthaltig ist. Es wird aufgezeigt, wie Sie
eigene Innovationen nahtlos in die Suite integrieren, ohne die Update-Fähigkeit des Gesamtsystems zu gefährden.

## Auf einen Blick

- **Lizenzrechtliche Unabhängigkeit:** Die Veröffentlichung unter der Apache 2.0 Lizenz garantiert, dass der Quellcode
  dauerhaft prüfbar, anpassbar und frei von Lizenzgebühren bleibt.
- **Vermeidung von Vendor-Lock-in:** Ein modulares LLM-Gateway ermöglicht den Austausch von Modell-Anbietern (z.B. Azure
  zu Google oder lokalem vLLM) rein durch Konfiguration.
- **Native Erweiterbarkeit:** Das «Controller-Pattern» erlaubt Entwicklern, eigene Dienste zu bauen, die automatisch
  erkannt und nahtlos in die Benutzeroberfläche und Infrastruktur integriert werden.
- **Sicheres Lifecycle-Management:** Durch «Version Pinning» in der Projektkonfiguration bleiben kundenspezifische
  Erweiterungen stabil, auch wenn die Kernplattform aktualisiert wird.
- **Zukunftssicherheit durch Standards:** Unterstützung moderner Protokolle wie dem Model Context Protocol (MCP) öffnet
  die Plattform für zukünftige KI-Tools und externe Entwicklungsumgebungen.

## Investitionsschutz durch Open Source und Standards

### Geschäftlicher Nutzen

Ein klassisches Risiko bei der Beschaffung von Enterprise-Software ist der «Vendor Lock-in». Kunden geraten in eine
Abhängigkeit, in der sie Preiserhöhungen, Lizenzänderungen oder Strategiewechsel des Herstellers hilflos ausgeliefert
sind. Im schlimmsten Fall stellt ein Anbieter den Betrieb ein, und das darauf aufgebaute Unternehmenswissen geht
verloren. CIOs und Einkäufer fordern daher Garantien für langfristige Verfügbarkeit und Unabhängigkeit. Eine Plattform
muss sicherstellen, dass das Unternehmen jederzeit Eigentümer seiner Architektur und Daten bleibt, unabhängig von
externen Marktkräften.

### Konzeptioneller Ansatz

Der Swiss AI Hub basiert auf der Philosophie der technologischen Souveränität. Dies wird primär durch die
Veröffentlichung unter der **Apache 2.0 Lizenz** gewährleistet. Diese liberale Open-Source-Lizenz garantiert, dass der
Quellcode der Plattform für den Mandanten einsehbar, modifizierbar und dauerhaft nutzbar ist. Ergänzend dazu setzt die
Architektur konsequent auf offene Industriestandards statt auf proprietäre Formate. Dies betrifft Schnittstellen,
Datenhaltung und Kommunikationsprotokolle, was eine nahtlose Portabilität und Interoperabilität gewährleistet.

### Technische Umsetzung im Swiss AI Hub

Die technische Basis bildet ein Stack aus bewährten Open-Source-Komponenten, die weltweit millionenfach im Einsatz sind
und keine «Black Boxes» darstellen.

- **Code-Transparenz und Auditierbarkeit:** Da der Kerncode offenliegt, können interne Sicherheitsteams oder externe
  Auditoren die Integrität der Software jederzeit verifizieren. Es gibt keine kompilierten Binaries unbekannter
  Herkunft.
- **Offene Datenhaltung:** Es werden keine proprietären Speicherformate verwendet. Vektordaten residieren in **Milvus**
  oder Azure AI Search, relationale Daten in **PostgreSQL** und Dateien in S3-kompatiblen Objektspeichern (z.B. MinIO).
  Ein Export der Daten ist durch Standard-Datenbank-Tools jederzeit möglich, was eine jederzeitige «Exit-Strategie»
  sichert.
- **Standard-APIs:** Die Schnittstellen basieren auf REST, gRPC und dem OpenAI-Standardformat. Dies bedeutet, dass
  Client-Anwendungen nicht mit proprietären SDKs verdrahtet werden müssen, sondern Standard-Bibliotheken nutzen können.
  Durch die Unterstützung des **Model Context Protocol (MCP)** öffnet sich die Plattform zudem für externe
  KI-Assistenten und IDEs, die den Plattformstatus über standardisierte Endpunkte inspizieren können.

## Modulare Architektur und Vermeidung von Modell-Lock-in

### Geschäftlicher Nutzen

Der Markt für Large Language Models (LLMs) ist volatil. Während heute vielleicht GPT-4 führend ist, könnten morgen
Modelle von Anthropic, Google oder spezialisierte Open-Source-Modelle das beste Preis-Leistungs-Verhältnis bieten. Eine
Anwendung, deren Code fest auf die API eines einzelnen Anbieters zugeschnitten ist, erfordert bei jedem Wechsel ein
teures Refactoring. Unternehmen benötigen eine Infrastruktur, die «modell-agnostisch» ist und es erlaubt, die
Intelligenz im Hintergrund auszutauschen, ohne die Geschäftsprozesse im Vordergrund zu stören oder
Sicherheitsrichtlinien neu definieren zu müssen.

### Konzeptioneller Ansatz

Die Plattform verfolgt das Prinzip der losen Kopplung. Kritische Komponenten – insbesondere das Sprachmodell, die
Vektordatenbank und der Embeddings-Provider – werden als austauschbare Module betrachtet. Eine Abstraktionsschicht
entkoppelt die Anwendungslogik von der spezifischen Implementierung. Dies erlaubt Administratoren, Komponenten durch
Konfiguration statt durch Programmierung zu wechseln. Das System ist somit «Batteries Included, but Swappable»: Es wird
mit funktionierenden Standardkomponenten geliefert, zwingt den Kunden aber nicht, diese dauerhaft zu nutzen.

### Technische Umsetzung im Swiss AI Hub

Zentrales Element für diese Flexibilität ist das **LLM-Gateway** (implementiert durch LiteLLM) sowie die modulare
Infrastruktur.

- **LLM-Abstraktion:** Das Gateway normalisiert die APIs von über 100 Anbietern. Ein Wechsel von Azure OpenAI zu Google
  Gemini oder zu einem lokalen Modell via **vLLM**, **llama.cpp** oder **Hugging Face Text Embedding Inference**
  erfordert lediglich eine Anpassung der YAML-Konfiguration (`model_list`). Die Agenten-Logik bleibt davon unberührt, da
  sie gegen eine vereinheitlichte Schnittstelle programmiert ist.
- **Routing-Strategien:** Die Konfiguration erlaubt komplexes Routing («usage-based-routing-v2»), um Lasten auf
  verschiedene Modelle zu verteilen oder Fallbacks zu definieren, falls ein Anbieter nicht erreichbar ist.
- **Infrastruktur-Schichten:** Auch Infrastrukturkomponenten wie der Message Bus (NATS) oder die Vektordatenbank sind
  modular eingebunden. Die Architektur erlaubt theoretisch den Austausch von Milvus gegen andere Vektorspeicher, sofern
  diese die internen Schnittstellenverträge erfüllen.

## Erweiterbarkeit durch SDK und Plugin-System

### Geschäftlicher Nutzen

Kein Standardprodukt kann die spezifischen Anforderungen jedes Unternehmens zu 100 Prozent abdecken. Banken benötigen
andere Integrationen als Spitäler oder Industrieunternehmen. Oft scheitern Plattformen daran, dass Anpassungen
(«Customizing») den Kerncode verändern, was zukünftige Updates unmöglich macht oder extrem verteuert. Die Anforderung
lautet daher: Maximale Anpassbarkeit bei gleichzeitiger Wahrung der Update-Fähigkeit des Kernsystems. Unternehmen müssen
in der Lage sein, eigene Geschäftslogik als Erweiterung zu bauen, die sich nahtlos in die Suite einfügt.

### Konzeptioneller Ansatz

Der Swiss AI Hub bietet ein Software Development Kit (SDK) und eine Plugin-Architektur, die Erweiterungen als
«First-Class Citizens» behandelt. Das bedeutet, dass selbst entwickelte Agenten oder Dienste nicht wie fremde Anhängsel
wirken, sondern sich optisch und funktional nicht von den nativen Komponenten unterscheiden. Das Architekturmuster
trennt strikt zwischen der **Kerninfrastruktur** (bereitgestellt durch die Plattform) und **benutzerdefinierten
Diensten** (entwickelt durch den Kunden). Erweiterungen nutzen die Infrastruktur (Auth, DB, Messaging), ohne sie zu
modifizieren.

### Technische Umsetzung im Swiss AI Hub

Die Erweiterbarkeit wird durch das **Controller-Pattern** und eine klare Trennung der Code-Repositories realisiert.

- **Controller-Integration:** Benutzerdefinierte Dienste erben von einer Basis-Controller-Klasse. Sie definieren ihre
  Metadaten (Name, Icon, Rechte) und API-Endpunkte. Die Plattform erkennt diese Dienste beim Start automatisch («Service
  Discovery») und integriert sie dynamisch in die Benutzeroberfläche und das Navigationsmenü.
- **Shared Infrastructure:** Eigene Erweiterungen müssen keine eigene Datenbank oder Authentifizierung mitbringen. Sie
  erhalten Zugriff auf NATS, MongoDB und den OIDC-Login der Plattform. Dies reduziert den Entwicklungsaufwand für
  interne Tools massiv, da Aspekte wie Logging, Metriken und Sicherheit bereits gelöst sind.
- **Frontend-Erweiterung:** Über generierte TypeScript-Clients und Vue-Komponenten können Entwickler eigene UIs bauen.
  Da diese denselben Technologie-Stack (Nuxt 3, Vue 3, PrimeVue) nutzen, fügen sie sich nahtlos in das Look-and-Feel der
  Suite ein.
- **Codegenerierung:** Um den Einstieg zu erleichtern, bietet das SDK Generatoren, die Boilerplate-Code für neue Dienste
  erstellen und so die Einhaltung der Plattformkonventionen sicherstellen.

## Lifecycle-Management und Update-Strategie

### Geschäftlicher Nutzen

Software altert. Ohne regelmässige Updates entstehen Sicherheitslücken und technologische Rückstände. Die Angst vor dem
«Breaking Change» – einem Update, das die eigene Anwendung lahmlegt – führt jedoch oft dazu, dass Systeme veralten.
Unternehmen benötigen eine Update-Strategie, die Stabilität garantiert. Es muss möglich sein, die zugrundeliegende
Plattform zu aktualisieren, um von Sicherheits-Patches und neuen Features zu profitieren, ohne dass die mühsam
entwickelten, kundenspezifischen Agenten und Workflows brechen.

### Konzeptioneller Ansatz

Der Swiss AI Hub löst dieses Problem durch eine strikte Trennung von **Core** (Plattform) und **Custom Code**
(Kundenanwendung) in Kombination mit semantischer Versionierung. Die Plattform entwickelt sich unabhängig von der
Kundenanwendung weiter. Die Kundenanwendung deklariert explizit, mit welcher Version des Cores sie kompatibel ist. Dies
verhindert, dass ein automatisches Plattform-Update ungewollt Inkompatibilitäten einführt. Updates werden bewusst und
kontrolliert durchgeführt.

### Technische Umsetzung im Swiss AI Hub

Das technische Management der Lebenszyklen erfolgt über Docker-Container und Python-Paketverwaltung.

- **Version Pinning:** In der Konfiguration des Kundenprojekts (`pyproject.toml`) wird die Abhängigkeit zum Core fixiert
  (z.B. `aihub-core = "v1.2.3"`). Ein Update des Cores erfordert eine aktive Änderung dieser Version durch den
  Entwickler, was Raum für Tests in einer Staging-Umgebung schafft.
- **Unabhängige Deployments:** Da Core-Dienste (API, Web, Dagster) und Kunden-Dienste (Agents, Pipelines) in separaten
  Containern laufen und als unabhängige Docker-Images (`ghcr.io/bbvch-ai/...`) bereitgestellt werden, können sie
  unabhängig voneinander aktualisiert werden. Bei Minor-Updates kann der Core aktualisiert werden, während die Agenten
  weiterlaufen.
- **Zero-Downtime-Potenzial:** Die Unterstützung von Rolling Updates in Container-Orchestrierungsplattformen und die
  Zustandslosigkeit der API-Komponenten ermöglichen es, neue Versionen bereitzustellen, ohne den laufenden Betrieb zu
  unterbrechen.
- **Rollback-Sicherheit:** Da jede Version als unveränderliches Docker-Image vorliegt, ist ein Zurücksetzen auf den
  vorherigen Stand bei Problemen trivial – es genügt das Ändern des Image-Tags in der `docker-compose.yml` und ein
  Neustart der Dienste.
