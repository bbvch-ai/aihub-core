# Executive Summary

## Die Lücke zwischen KI-Prototyp und Produktionsrealität

Künstliche Intelligenz hat sich von einem experimentellen Technologiefeld zu einem strategischen Wettbewerbsfaktor
entwickelt. Doch Schweizer Unternehmen stehen vor einer signifikanten Hürde, die oft erst nach den ersten Erfolgen
sichtbar wird: Es ist trivial, an einem Nachmittag einen beeindruckenden KI-Prototypen mit Bibliotheken wie LangChain zu
erstellen – dies ist der «Day 1». Extrem komplex hingegen ist der «Day 2»: diesen Prototypen sicher, compliance-konform
und skalierbar zu betreiben.

Organisationen sehen sich heute oft mit einer fragmentierten Landschaft konfrontiert. Während ein Team Python-Skripte
für Azure OpenAI nutzt, baut ein anderes isolierte RAG-Systeme, und die Compliance-Abteilung hat keinen zentralen
Einblick in den Datenabfluss. Auf der einen Seite stehen reine Code-Bibliotheken, die zwar flexibel sind, aber keine
Infrastruktur für Sicherheit, Monitoring oder Benutzerverwaltung bieten. Auf der anderen Seite locken grosse
Cloud-Anbieter mit Komplettlösungen, die jedoch einen Vendor Lock-in erzwingen und oft im Widerspruch zu strengen
Schweizer Anforderungen an die Datensouveränität stehen.

Der **Swiss AI Hub** schliesst diese Lücke. Es handelt sich nicht um einen weiteren KI-Dienst im Abonnement, sondern um
eine vollständige Enterprise-KI-Infrastruktur, die Sie besitzen, kontrollieren und in Ihrer eigenen Umgebung betreiben.
Sie erhalten die Vollständigkeit einer Managed-Cloud-Plattform kombiniert mit der Kontrolle und Unabhängigkeit einer
Eigenentwicklung.

## Infrastruktur als Produkt: Der «Day 2»-Vorteil

Die grössten Herausforderungen bei der Einführung von KI treten erst nach der ersten Demonstration auf. Sobald ein
System den geschützten Rahmen verlässt, stellen sich kritische Fragen zur Authentifizierung, Kostenkontrolle,
Daten-Ingestion und Nachvollziehbarkeit (Auditability). Wer diese Aspekte selbst entwickelt, baut keine KI-Lösungen,
sondern investiert wertvolle Ressourcen in den mühsamen Nachbau von Basisinfrastruktur.

Der Swiss AI Hub liefert diese Infrastruktur als fertiges Produkt («Infrastructure as a Product»). Die Plattform
integriert Best-in-Class Open-Source-Komponenten zu einem harmonisierten Gesamtsystem, das via Docker Compose oder
Kubernetes bereitgestellt wird. Anstatt Monate mit der Integration von Einzelkomponenten zu verbringen, erhalten
IT-Teams ein startklares System, das Enterprise-Funktionen wie Single Sign-On (SSO) und rollenbasierte
Zugriffskontrollen bereits mitbringt.

Die technische Umsetzung im Swiss AI Hub basiert auf einer orchestrierten Zusammenstellung bewährter Technologien, die
nahtlos ineinandergreifen:

- **Zentrales LLM-Gateway & Speicher:** LiteLLM fungiert als vereinheitlichtes Gateway für den Zugriff auf diverse
  Modelle und abstrahiert die Anbieterkomplexität, während SeaweedFS eine S3-kompatible Objektspeicherung für die lokale
  Datenhaltung bereitstellt.
- **Daten-zu-Wissen-Pipeline:** Dagster orchestriert komplexe Datenpipelines, während Docling das Parsing von Dokumenten
  (PDFs, Office-Dateien) übernimmt. Diese werden in einer Vektordatenbank (Milvus) für semantische Suchen und
  Retrieval-Augmented Generation (RAG) indiziert.
- **Architektur & Observability:** NATS sorgt als Messaging-System für eine ereignisgesteuerte Architektur. Phoenix und
  OpenTelemetry gewährleisten vollständige Transparenz und Tracing jeder einzelnen KI-Entscheidung bis hin zum
  ursprünglichen Prompt.

## Schweizer Datensouveränität: Vertrauen durch deterministische Workflows

Für Entscheidungsträger in der Schweiz ist die Kontrolle über den Datenfluss oft nicht verhandelbar. Viele
internationale Lösungen scheitern an der Anforderung, dass sensible Unternehmensdaten den Rechtsraum der Schweiz oder
das eigene Firmennetzwerk nicht verlassen dürfen. Zudem benötigen Unternehmen Vertrauen in die Entscheidungen der KI,
was durch völlig offene Agenten-Loops, die unvorhersehbare Aktionen ausführen können, oft untergraben wird.

Der Swiss AI Hub adressiert dieses Bedürfnis durch das Prinzip der **Closed Workflows**. Anstatt Agenten freie Hand zu
lassen, folgen diese definierten Pfaden innerhalb eines Agenten-Bauplans. Ein Agent kann nicht eigenmächtig entscheiden,
auf nicht autorisierte Daten zuzugreifen oder unerwartete Aktionen auszuführen. Ergänzt wird dies durch Mechanismen wie
**Presidio**, die für die Erkennung und Anonymisierung von Personenidentifizierbaren Informationen (PII) sorgen, noch
bevor diese ein Modell erreichen. Vertrauen entsteht hier gemäss der Gleichung: **Vertrauen = Vorhersagbarkeit +
Sichtbarkeit + Kontrolle**.

Die Architektur ermöglicht den Betrieb lokaler Open-Source-Modelle (wie Mistral, Llama oder DeepSeek) vollständig
On-Premise. Sensible Unternehmensdaten verbleiben physisch in Ihrer Infrastruktur, gesichert durch lokale Datenbanken
wie FerretDB und ValKey. Gleichzeitig erlaubt das System hybride Ansätze: Unkritische Anfragen können an leistungsfähige
Cloud-Modelle geleitet werden, während vertrauliche Dokumente lokal verarbeitet werden.

## Plattform und SDK: Effizienz durch Standardisierung

Ein häufiges Problem in Unternehmen ist die Entstehung von «Schatten-KI», wo verschiedene Abteilungen isolierte Lösungen
mit unterschiedlichen Standards bauen. Dies führt zu Sicherheitsrisiken, ineffizientem Ressourceneinsatz und fehlender
Wartbarkeit.

Der Swiss AI Hub löst dies durch die strategische Trennung von Plattform (Infrastruktur) und SDK (Entwicklung):

1. **Die Plattform** stellt die zentralen Dienste bereit: Authentifizierung, Datenbanken, Monitoring, Vektorspeicher und
   LLM-Gateways.
2. **Das SDK** ermöglicht Entwicklern, sich rein auf die Geschäftslogik zu konzentrieren.

Wer mit dem SDK entwickelt, erbt automatisch alle Sicherheits- und Governance-Funktionen der Plattform. Ein neuer
KI-Agent muss keine eigene Benutzerverwaltung implementieren oder Datenbankverbindungen managen – die Plattform stellt
dies bereit. Dies beschleunigt die Entwicklung drastisch und garantiert gleichzeitig, dass alle Anwendungen im
Unternehmen denselben Compliance- und Sicherheitsstandards entsprechen.

## Transparenz, Kostenkontrolle und Investitionssicherheit

Neben der Sicherheit ist die wirtschaftliche Planbarkeit ein entscheidender Faktor für das C-Level. Cloud-basierte
KI-Dienste bergen das Risiko intransparenter und schnell steigender Kosten, während reine Bibliotheken (wie LangChain)
hohe Personalkosten für die Infrastrukturentwicklung verursachen.

Der Swiss AI Hub begegnet diesem Risiko mit umfassender Governance. Über das zentrale LLM-Gateway lassen sich Budgets
und Limits auf Ebene von Benutzern, Teams oder Modellen definieren. Ein Echtzeit-Dashboard schafft Transparenz darüber,
welche Abteilungen oder Prozesse welche Kosten verursachen. Da die Plattform unter der **Apache 2.0 Lizenz** als Open
Source zur Verfügung steht, entfallen zudem Lizenzgebühren für die Software selbst. Sie zahlen lediglich für die
Infrastruktur, auf der Sie das System betreiben.

Diese Offenheit garantiert zudem Freiheit von Herstellerabhängigkeiten (Vendor Lock-in). Der Quellcode gehört Ihnen.
Sollten sich Ihre Anforderungen ändern, haben Sie die Freiheit, die Plattform anzupassen, zu erweitern oder auf andere
Hardware zu migrieren. Sie erwerben keine «Black Box», sondern das fundamentale Eigentum an Ihrer KI-Strategie.

## Zusammenfassung für Entscheidungsträger

Der Swiss AI Hub ist die Antwort auf die Frage, wie Schweizer Unternehmen KI-Technologie sicher, skalierbar und souverän
nutzen können, ohne die Kontrolle an US-Cloud-Giganten abzugeben oder in endlosen Eigenentwicklungen zu versinken.

Die Plattform liefert:

- **Produktionsreife:** Sofortige Verfügbarkeit von Security, Monitoring, Auth und Governance («Day 2 ready»).
- **Souveränität:** Vollständige Kontrolle über Datenstandort (On-Premise/Cloud) und Datenfluss.
- **Wirtschaftlichkeit:** Transparente Kostenstrukturen, keine Lizenzkosten, keine versteckten Margen.
- **Zukunftssicherheit:** Eine offene Architektur auf Basis von Docker und Kubernetes, die mit Ihren Anforderungen
  wächst.

Mit dem Swiss AI Hub transformieren Sie KI von einem riskanten Experiment zu einer beherrschbaren, unternehmenseigenen
Infrastrukturkomponente. Die folgenden Kapitel dieses Whitepapers detaillieren die technischen und prozessualen Aspekte
dieser Lösung.
