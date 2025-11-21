# Kapitel 03: Datensouveränität und vollständige Kundenkontrolle

Die digitale Transformation durch Künstliche Intelligenz birgt für Schweizer Unternehmen ein immenses Potenzial. Doch
die Realisierung dieses Potenzials ist untrennbar mit der Frage der Datensouveränität verbunden. In einem Umfeld, das
von strengen Datenschutzgesetzen und dem Bedürfnis nach Kontrolle über sensible Unternehmensdaten geprägt ist, benötigen
Organisationen eine Plattform, die uneingeschränkte Hoheit über Daten und Informationsflüsse garantiert. Das vorliegende
Kapitel legt dar, wie der Swiss AI Hub diese entscheidenden Anforderungen erfüllt, indem er maximale Data Residency,
Unabhängigkeit von Modell-Anbietern und vollständige Transparenz über KI-Entscheidungen sicherstellt.

## 1. Souveräne Bereitstellungsmodelle: Volle Kontrolle über die Datenresidenz

Die Fähigkeit, sensible Unternehmensdaten innerhalb der eigenen geografischen und rechtlichen Grenzen zu halten, ist für
Schweizer Organisationen von fundamentaler Bedeutung. Der Swiss AI Hub adressiert diese Anforderung durch flexible und
souveräne Bereitstellungsoptionen, die eine lückenlose Datenhoheit gewährleisten.

### Mehrwert und Nutzen: Garantierte Datenresidenz und Ausschluss externer Zugriffe

Traditionelle Cloud-KI-Dienste verarbeiten Daten oft auf Servern ausserhalb der Schweiz, was bei sensiblen Informationen
ein erhebliches Compliance- und Vertrauensrisiko darstellt. Der Swiss AI Hub beseitigt diese Bedenken, indem er es
Organisationen ermöglicht, die physische Speicherung und Verarbeitung ihrer Daten vollständig selbst zu kontrollieren.
Dies schützt nicht nur vor unkontrolliertem Datenabfluss ins Ausland, sondern eliminiert auch jeglichen technischen oder
administrativen Zugriff des Plattformanbieters auf Inhalte oder Wissensdatenbanken. Das Ergebnis ist eine maximale
Datensouveränität, die den strengsten Vorgaben entspricht und die Grundlage für eine vertrauenswürdige KI-Strategie
bildet.

### Konzepte & Prozesse: Single-Tenant-Isolation und flexible Hosting-Optionen

Der Swiss AI Hub ist primär für Single-Tenant-Bereitstellungen konzipiert. Dies bedeutet, dass jede Organisation eine
vollständige, eigenständige Instanz der Plattform betreibt, einschliesslich dedizierter Datenbanken, Vektor-Stores und
Dateispeicher. Im Gegensatz zu Multi-Tenant-SaaS-Plattformen, bei denen Ressourcen gemeinsam genutzt werden, erhalten
Kunden einen eigenen, vollständig isolierten Stack.

Die Plattform unterstützt zudem einen Air-Gapped-Betrieb, bei dem die Instanz ohne ausgehende Internetverbindung
betrieben werden kann, sofern lokal gehostete Sprachmodelle (LLMs) verwendet werden. Diese Option ist für Umgebungen mit
höchsten Sicherheitsanforderungen, wie sie oft im öffentlichen Sektor bestehen, unerlässlich. Die Kontrolle über die
Administration der Plattform liegt dabei vollständig bei der auftraggebenden Organisation, es sei denn, ein Managed
Service-Modell mit einem Schweizer Hoster wird explizit gewählt.

### Technische Umsetzung im Swiss AI Hub: On-Premise, Private Cloud und Schweizer SaaS

Der Swiss AI Hub kann flexibel in verschiedenen Umgebungen gehostet werden, um den individuellen Sicherheits- und
Residenzanforderungen gerecht zu werden:

- **On-Premise (eigener Server):** Organisationen betreiben den AI Hub auf ihren eigenen Servern im eigenen
  Rechenzentrum. Die gesamte Infrastruktur, einschliesslich CPU, RAM, Speicher und optional NVIDIA-GPUs für lokale
  LLM-Inferenz, liegt in der vollständigen Kontrolle des Kunden. Dies ermöglicht einen Air-Gapped-Betrieb und eliminiert
  jegliche Cloud-Abhängigkeit. Die Plattform nutzt standardmässig robuste Datenbanken wie FerretDB/PostgreSQL und
  Vektor-Stores wie Milvus für die Datenhaltung.
- **Private Cloud (eigene Cloud):** Die Bereitstellung erfolgt in der eigenen Cloud-Umgebung des Kunden, sei es bei
  einem Schweizer Cloud-Anbieter oder Hyperscaler wie Azure, AWS oder GCP. Dabei bleiben alle Daten im Cloud-Konto des
  Kunden und unter dessen Kontrolle, mit der Option, spezifische Regionen (z.B. Schweiz) für die Datenresidenz zu
  wählen.
- **SaaS (Schweizer Cloud-Hosting):** Als Alternative zu einer selbstverwalteten Bereitstellung bietet die bbv als
  Plattformanbieter das Hosting und die Verwaltung des AI Hub auf einer Schweizer Cloud-Infrastruktur an. In diesem Fall
  kümmert sich bbv um Bereitstellung, Updates, Backups und Monitoring, wobei die Daten stets in der Schweiz und unter
  Schweizer Rechtshoheit verbleiben.

Die Datenisolation ist ein Kernmerkmal: Die Daten jedes Tenants bleiben in der jeweiligen Instanz. Es gibt keine
gemeinsame Datenbank oder gemeinsamen Vektor-Store zwischen Organisationen, was die Anforderungen des revDSG und der
DSGVO an die Datenisolation vollständig erfüllt. Bei einer Multi-Tenant-Bereitstellung erhalten zwar mehrere Tenants
eine eigene isolierte Infrastruktur, können aber optional gemeinsame, zustandslose LLM-Backend-Ressourcen nutzen, ohne
dass Prompts, Antworten oder Benutzerdaten die Grenzen der jeweiligen Tenant-Instanz verlassen.

## 2. Herstellerunabhängigkeit und anpassbare KI-Modellnutzung

Die dynamische Entwicklung im Bereich der Künstlichen Intelligenz erfordert von Unternehmen Agilität und die Freiheit,
stets die besten verfügbaren KI-Modelle einzusetzen, ohne dabei von einem einzelnen Anbieter abhängig zu sein.

### Mehrwert und Nutzen: Strategische Unabhängigkeit und nachhaltige Investitionssicherheit

Das Risiko eines Vendor Lock-in und die Abhängigkeit von einzelnen Hyperscalern stellen eine erhebliche strategische
Herausforderung dar. Der Swiss AI Hub entkoppelt die Anwendungsebene von spezifischen KI-Modellen und -Anbietern. Dies
sichert die Freiheit, stets die optimalen LLMs (proprietär oder Open Source) zu wählen, die den Anforderungen an
Leistung, Kosten und Datensouveränität am besten entsprechen. Diese Flexibilität gewährleistet nicht nur eine
langfristige Investitionssicherheit, sondern auch die strategische Handlungsfähigkeit der Organisation, selbst bei
marktspezifischen oder technologischen Paradigmenwechseln.

### Konzepte & Prozesse: Der LLM-Proxy und Open Standards

Ein zentrales Element ist der LLM-Proxy (LiteLLM), der als vereinheitlichtes Gateway zu allen Sprachmodell-Anbietern
dient. Er abstrahiert anbieterspezifische APIs und ermöglicht es dem Plattform-Code, mit einer konsistenten
Schnittstelle zu interagieren, unabhängig vom zugrunde liegenden Modell (z.B. OpenAI, Google, Anthropic, Azure OpenAI
oder selbst gehostete Modelle). Das intelligente Routing leitet Anfragen basierend auf Konfiguration, Kostenoptimierung
oder Lastverteilung an die geeigneten Modelle weiter.

Darüber hinaus setzt der Swiss AI Hub auf offene, standardisierte Formate für die Speicherung von Vektordaten und
Konfigurationen. Dies verhindert, dass Unternehmenswissen in proprietären Datensilos gefangen ist und ermöglicht einen
Systemwechsel oder Datenexport zu jeder Zeit. Die Modularität der Architektur erlaubt den Austausch einzelner
Komponenten wie Vektor-Stores oder LLMs, ohne die gesamte Lösung neu aufbauen zu müssen.

### Technische Umsetzung im Swiss AI Hub: LiteLLM und modulare Komponentenarchitektur

Der LLM-Proxy (LiteLLM) bietet eine OpenAI-kompatible API, die eine breite Palette von Modellen unterstützt,
einschliesslich selbst gehosteter Lösungen wie vLLM, llama.cpp oder HF-TEI. Dies ermöglicht auch den Betrieb in
Air-Gapped-Umgebungen ohne Internetverbindung. Die Plattform kann problemlos mehrere LLM-Anbieter gleichzeitig nutzen
und Anfragen intelligent zwischen ihnen routen, beispielsweise für Kostenoptimierung oder den Einsatz spezialisierter
Modelle.

Für die RAG-Konfiguration (Retrieval Augmented Generation) können Organisationen eigene Datenpipelines über das SDK
erstellen und anpassen, um verschiedene Datenquellen (Dateien, Datenbanken, APIs) anzubinden. Die in Stufe 2 der
Architektur beschriebenen Pipelines verarbeiten Dokumente, erstellen Embeddings und speichern diese in Vektordatenbanken
(z.B. Milvus). Die Kontrolle über diese Datenquellen und die RAG-Konfiguration liegt vollständig beim Kunden. Die
Plattform ist zudem über das Model Context Protocol (MCP) offen für die sichere Integration von Agenten aus anderen
Systemen, was die Interoperabilität weiter fördert.

## 3. Umfassende Zugriffssteuerung und Transparenz

Ein vertrauenswürdiges KI-System erfordert nicht nur die Kontrolle über Daten, sondern auch über deren Nutzung und die
Nachvollziehbarkeit von KI-generierten Entscheidungen.

### Mehrwert und Nutzen: Granulare Zugriffsverwaltung und eliminierte Black-Box-Effekte

In komplexen Unternehmensumgebungen ist eine feingranulare Kontrolle unerlässlich, wer auf welche KI-Funktionen und
Daten zugreifen darf. Gleichzeitig müssen Unternehmen sicherstellen, dass KI-Entscheidungen nicht zu intransparenten
"Black-Box"-Effekten führen. Der Swiss AI Hub bietet ein robustes System für rollenbasierte Zugriffssteuerung (RBAC) und
umfassende Transparenzfunktionen. Dies stellt sicher, dass Benutzer nur relevante Funktionen sehen, während alle
KI-Operationen nachvollziehbar und prüfbar sind. Menschliche Überprüfungsschritte (Human-in-the-Loop) können zudem
obligatorisch integriert werden, um die Verantwortung bei kritischen Entscheidungen zu sichern.

### Konzepte & Prozesse: Hierarchisches RBAC und Human-in-the-Loop

Die Plattform implementiert eine ausgeklügelte, berechtigungsbasierte Zugriffssteuerung, die das Benutzererlebnis
dynamisch an das Autorisierungslevel jedes Einzelnen anpasst. Berechtigungen folgen einer hierarchischen Punkt-Notation
(`aihub.[user|admin].<service>.<resource_type>.<resource_id>`) und unterstützen Wildcards für flexible Zuweisungen.
Administratoren können Rollen definieren und Benutzern zuweisen, um den Zugriff auf spezifische Agenten, Dienste oder
Prozesse zu steuern.

Für eine transparente Entscheidungsfindung integriert die Plattform Human-in-the-Loop-Funktionen, insbesondere in
komplexen Prozessautomatisierungen (Stufe 3 der Architektur). Wenn ein Schritt menschliches Urteilsvermögen erfordert,
wird im Arbeitsbereich des relevanten Benutzers eine Aufgabe erstellt, die die Analyse der KI, das Quelldokument und den
Kontext für die Entscheidung bereitstellt.

### Technische Umsetzung im Swiss AI Hub: Access Checker, Audit-Trails und PII-Anonymisierung

Die Zugriffssteuerung erfolgt im Backend über eine `AccessChecker`-Komponente, die sicherstellt, dass
Sicherheitsdurchsetzung nicht durch clientseitige Manipulation umgangen werden kann. Die Benutzeroberfläche zeigt nur
Funktionen an, für die der Benutzer autorisiert ist. Die Authentifizierung lässt sich nahtlos in bestehende
Unternehmens-Identitätssysteme wie Azure AD oder Keycloak über Standards wie OAuth 2.0 oder OIDC integrieren.

Jede Berechtigungsbewertung und jede Benutzeraktion generiert detaillierte Audit-Log-Einträge, die dokumentieren, wer
wann welche Aktion ausgeführt hat. Diese Audit-Trails, kombiniert mit der tiefen Observability durch OpenTelemetry und
Phoenix Tracing, ermöglichen eine lückenlose Nachvollziehbarkeit jeder Agentenaktion und jedes LLM-Aufrufs. Die
Plattform erfasst dabei auch die Herkunft jedes Embeddings zurück zu seinem Quelldokument, was eine präzise
Daten-Lineage für regulatorische Audits sicherstellt. Darüber hinaus unterstützt die Plattform die Erkennung und
Anonymisierung sensibler Daten (PII) durch Presidio, bevor diese externe LLMs erreichen.

## 4. Compliance und Rechte der betroffenen Person

Die Einhaltung von Datenschutzgesetzen wie dem revDSG und der DSGVO ist für Schweizer Unternehmen nicht verhandelbar.
Der Swiss AI Hub bietet eine technische Grundlage, um diesen Anforderungen gerecht zu werden und die Rechte der
betroffenen Personen umfassend zu unterstützen.

### Mehrwert und Nutzen: Regulatorische Sicherheit und Vertrauen

Unsicherheiten bei der Einhaltung von Datenschutzvorschriften können Innovationsprojekte im Keim ersticken. Der Swiss AI
Hub wurde mit Blick auf die strengen Anforderungen des revDSG und der DSGVO entwickelt. Er bietet die technischen
Massnahmen und Konfigurationsmöglichkeiten, die Organisationen benötigen, um ihre Compliance-Verantwortung wahrzunehmen.
Dies schafft das notwendige Vertrauen für den Einsatz von KI in sensiblen Bereichen und minimiert rechtliche Risiken.

### Konzepte & Prozesse: DSG und DSGVO-Prinzipien

Die Plattform unterstützt die Einhaltung der zentralen Datenschutzprinzipien: Rechtmässigkeit, Fairness und Transparenz
(durch Audit-Trails und Tracing), Zweckbindung, Datenminimierung (durch RBAC und Namespace-Isolation), Richtigkeit
(durch Versionskontrolle), Speicherbegrenzung (ephemere Daten, konfigurierbare Aufbewahrungsfristen) sowie Integrität
und Vertraulichkeit (durch Verschlüsselung und Zugriffskontrollen). Für Schweizer Organisationen ist relevant, dass ein
EU-Angemessenheitsbeschluss für die Schweiz besteht, der den freien Fluss personenbezogener Daten zwischen der EU und
der Schweiz ohne zusätzliche Schutzmassnahmen ermöglicht.

Die Plattform unterstützt zudem die Rechte der betroffenen Personen gemäss DSGVO und revDSG:

- **Auskunftsrecht (Art. 15 DSGVO / Art. 25 revDSG):** Nutzer können Kopien ihrer Daten anfordern; die Plattform bietet
  APIs für Benutzerprofile, Konversations-Threads und Audit-Logs.
- **Recht auf Berichtigung (Art. 16 DSGVO / Art. 32 revDSG):** Administratoren können Benutzerprofile korrigieren.
  Thread-Nachrichten und Audit-Logs bleiben unveränderlich, um die Integrität der Audit-Trails zu bewahren.
- **Recht auf Löschung / "Recht auf Vergessenwerden" (Art. 17 DSGVO / Art. 32 revDSG):** Die Plattform unterstützt das
  Entfernen von Nutzern aus Threads; ephemere Daten werden nach 30 Tagen automatisch gelöscht.
- **Recht auf Datenübertragbarkeit (Art. 20 DSGVO / Art. 28 revDSG):** Gilt für direkt bereitgestellte Daten
  (Nachrichten, Uploads) in maschinenlesbarem Format, nicht für KI-generierte oder abgeleitete Daten.
- **Recht auf Einschränkung der Verarbeitung (Art. 18 DSGVO / Art. 32 revDSG):** Administratoren können Konten über RBAC
  sperren.
- **Widerspruchsrecht (Art. 21 DSGVO / Art. 28 revDSG):** Der Entzug von Berechtigungen über RBAC stoppt die
  Verarbeitung.

Das Consent-Management (Einwilligung) als Rechtsgrundlage für die Verarbeitung von Daten ist eine organisatorische
Verantwortung, die die Plattform durch entsprechende Mechanismen zur Dokumentation und Steuerung unterstützt.

### Technische Umsetzung im Swiss AI Hub: Privacy by Design und Meldeverfahren

Der Swiss AI Hub implementiert "Privacy by Design" durch obligatorische TLS/SSL-Verschlüsselung,
Default-Deny-Zugriffskontrolle, automatische 30-Tage-Löschung temporärer Daten und umfassendes Audit-Logging. Für
Hochrisikoprofiling, wie es das revDSG erfordert, bietet die Plattform Human-in-the-Loop-Funktionen, Phoenix-Tracing und
Quellenzuordnung.

Im Falle einer Datenschutzverletzung (Artikel 33/34 DSGVO; Artikel 24 revDSG) stellt die Plattform Audit-Protokolle,
Benutzerzugriffsberichte, Überwachungs-, Alarmierungs- und Sicherungsfunktionen bereit, um die Untersuchung,
Dokumentation und fristgerechte Meldung zu unterstützen. Obwohl das revDSG keine feste Frist nennt, wird in der Praxis
oft die 72-Stunden-Frist der DSGVO als Richtwert gesehen. Das Hosting in der Schweiz vermeidet zudem die komplexen
Anforderungen an internationale Datenübermittlungen, die sonst geeignete Schutzmassnahmen wie Standardvertragsklauseln
erfordern würden.

## 5. Nachhaltige Investitionssicherheit durch Offenheit

Die Langfristigkeit einer KI-Strategie hängt massgeblich von der Offenheit und Anpassungsfähigkeit der zugrunde
liegenden Plattform ab.

### Mehrwert und Nutzen: Eliminierung von Vendor Lock-in und Zukunftsfähigkeit

Proprietäre Plattformen bergen das Risiko, dass Unternehmen langfristig an einen Anbieter gebunden werden, was Kosten,
Flexibilität und Innovationsfähigkeit beeinträchtigt. Der Swiss AI Hub eliminiert diese Risiken durch ein konsequentes
Open-Source-Modell. Dies sichert nicht nur maximale Flexibilität und Kontrolle über die Technologie, sondern auch eine
nachhaltige Investitionssicherheit. Unternehmen können sich darauf verlassen, dass ihre KI-Infrastruktur auch bei
zukünftigen technologischen Entwicklungen oder einem hypothetischen Marktaustritt einzelner Komponentenanbieter
weiterhin funktionsfähig und anpassbar bleibt.

### Konzepte & Prozesse: Open-Source-Lizenz und offene Standards

Der Swiss AI Hub wird unter der Apache 2.0 Lizenz veröffentlicht, was maximale Transparenz, Prüfbarkeit und
Anpassbarkeit des Codes gewährleistet. Dieses Open-Source-Modell bedeutet, dass der Code den Organisationen gehört, auf
jeder Infrastruktur ausgeführt und bei Bedarf modifiziert werden kann. Es fallen keine Lizenzgebühren an, lediglich die
Kosten für die Infrastruktur, auf der die Plattform betrieben wird.

Die Architektur basiert konsequent auf offenen Standards und Protokollen. Dies umfasst nicht nur die APIs für
KI-Modelle, sondern auch die Speicherung von Vektordaten und Konfigurationen in allgemein zugänglichen Formaten.

### Technische Umsetzung im Swiss AI Hub: Modularität und Exportierbarkeit

Die Plattform ist so konzipiert, dass einzelne Kernkomponenten wie Datenbanken (FerretDB/PostgreSQL), Vektor-Stores
(Milvus oder Azure AI Search) und LLM-Provider flexibel ausgetauscht oder ergänzt werden können. Das vereinheitlichte
LLM-Gateway ermöglicht den Wechsel zwischen verschiedenen Sprachmodellen ohne Code-Änderungen. Diese Modularität in
Verbindung mit der Nutzung offener Protokolle (z.B. OTLP für Observability) sichert die technologische Unabhängigkeit.

Alle Daten, die innerhalb des Swiss AI Hub gespeichert werden, sind jederzeit exportierbar und in anderen Systemen
nutzbar. Das Recht auf Datenübertragbarkeit (Art. 20 DSGVO, Art. 28 revDSG) wird durch die Bereitstellung von Daten in
maschinenlesbaren Formaten unterstützt, insbesondere für vom Nutzer direkt bereitgestellte Inhalte wie Nachrichten und
Uploads. Die Open-Source-Natur der Plattform und die konsequente Verwendung offener Standards stellen sicher, dass das
investierte Know-how und die entwickelten Anwendungen langfristig nutzbar sind und nicht an proprietäre Ökosysteme
gebunden bleiben.
