# Executive Summary

Der Swiss AI Hub löst das zentrale Dilemma, dem sich Schweizer Unternehmen bei der Einführung künstlicher Intelligenz
gegenübersehen: Wie lassen sich die Vorteile moderner Sprachmodelle nutzen, ohne die Kontrolle über sensible Daten an
ausländische Cloud-Anbieter abzugeben oder Jahre an Entwicklungszeit in den Aufbau eigener Infrastruktur zu investieren?
Während Prototypen heute an einem Nachmittag erstellt sind, scheitern viele Projekte an der Hürde zur Produktionsreife –
an Fragen der Sicherheit, der Kostenkontrolle und der Integration in bestehende Geschäftsprozesse.

Dieses Whitepaper präsentiert eine Lösung, die diese Lücke schliesst. Der Swiss AI Hub ist nicht bloss eine weitere
Programmbibliothek, sondern eine vollständige Enterprise-KI-Infrastruktur, die Organisationen besitzen, kontrollieren
und innerhalb von 30 Minuten in Betrieb nehmen können. Durch die konsequente Ausrichtung auf Schweizer Werte wie
Datensouveränität und Transparenz sowie eine Architektur, die auf offenen Standards basiert, bietet die Plattform eine
zukunftssichere Basis für die KI-Transformation.

## Auf einen Blick

- **Vollständige Infrastruktur statt Baukasten:** Eine produktionsreife Plattform, die «Day 2»-Probleme wie
  Authentifizierung, Kostenkontrolle und Monitoring bereits im Standard löst.
- **Garantierte Schweizer Datensouveränität:** Die Daten verbleiben physisch in der Schweiz und innerhalb Ihres
  Sicherheitsperimeters; der Hub ist vollständig «Self-Hosted»-fähig.
- **Beschleunigte Einführung durch das Stufenmodell:** Ein strukturierter Pfad führt Organisationen sicher vom einfachen
  KI-Zugang bis zur komplexen Prozessautomatisierung.
- **Kein Vendor Lock-in:** Dank Open-Source-Architektur (Apache 2.0) und Modell-Agnostik bleiben Unternehmen unabhängig
  von spezifischen KI-Providern.
- **Vertrauen durch «Closed Workflows»:** Deterministische Agenten-Abläufe sorgen für Vorhersagbarkeit und erfüllen
  höchste Compliance-Anforderungen.

## Strategische Datensouveränität und Schweizer Compliance

### Geschäftlicher Nutzen

Für Schweizer Organisationen, insbesondere in regulierten Sektoren wie dem Finanzwesen, dem Gesundheitswesen oder der
öffentlichen Verwaltung, ist der Einsatz öffentlicher KI-Dienste oft mit untragbaren Risiken verbunden. Das Hochladen
vertraulicher Unternehmensdaten in die Cloud globaler Hyperscaler kollidiert häufig mit dem revidierten Schweizer
Datenschutzgesetz (revDSG) oder internen Compliance-Vorgaben. Dies führt dazu, dass Innovationsprojekte blockiert
werden. Der Swiss AI Hub löst diesen Konflikt, indem er vollständige Datensouveränität garantiert. Unternehmen müssen
sich nicht länger zwischen technologischer Innovation und Rechtssicherheit entscheiden; sie erhalten die Fähigkeit,
modernste KI-Modelle zu nutzen, während die Datenhoheit uneingeschränkt im eigenen Unternehmen verbleibt.

### Konzeptioneller Ansatz

Das zugrundeliegende Prinzip ist die absolute Kontrolle über den Speicherort und den Fluss der Daten. Im Gegensatz zu
SaaS-Lösungen ist der Swiss AI Hub als Infrastruktur konzipiert, die der Kunde selbst betreibt (Self-Hosted). Ob
On-Premise auf eigenen Servern oder in einer privaten Schweizer Cloud: Die Daten verlassen niemals den vom Mandanten
definierten Sicherheitsperimeter. Dieses Konzept ermöglicht auch den Einsatz lokaler Open-Source-Modelle für
hochsensible Personenidentifizierbare Informationen (PII), während weniger kritische Anfragen bei Bedarf über ein
kontrolliertes Gateway an externe Anbieter geleitet werden können.

### Technische Umsetzung im Swiss AI Hub

Technisch realisiert der Swiss AI Hub dies durch eine containerisierte Architektur. Kernkomponenten wie die
Vektordatenbank (Milvus) für die Speicherung von Unternehmenswissen und die Daten-zu-Wissen-Pipeline operieren lokal.
Zudem integriert die Plattform Presidio zur automatischen Erkennung und Anonymisierung von PII, bevor Daten an ein
Modell gesendet werden. Das integrierte LLM-Gateway fungiert als zentrale Schleuse, die den Datenfluss überwacht und
sicherstellt, dass alle Interaktionen den Schweizer Datenschutzstandards entsprechen.

## Beschleunigte Wertschöpfung durch das Stufenmodell

### Geschäftlicher Nutzen

Viele KI-Initiativen scheitern, weil sie versuchen, komplexe Automatisierungen einzuführen, bevor die organisatorische
Basis steht. Zudem unterschätzen Unternehmen oft den Aufwand für den produktiven Betrieb – den sogenannten «Day 2». Der
Swiss AI Hub reduziert dieses Risiko durch ein modulares Stufenmodell. Es ermöglicht einen schnellen Start mit minimalem
Investitionsrisiko und skaliert mit der Reife der Organisation. Dies verkürzt die Time-to-Value drastisch, da die
Infrastruktur nicht neu erfunden werden muss, sondern als «Batteries-included»-Produkt bereitsteht.

### Konzeptioneller Ansatz

Der Hub verfolgt einen evolutionären Pfad in drei Stufen: Stufe 1 etabliert einen sicheren, zentralen Zugang zu
KI-Modellen für alle Mitarbeitenden. Stufe 2 reichert diese Intelligenz durch die Anbindung von Unternehmensdaten
(Retrieval-Augmented Generation, RAG) an, wodurch kontextspezifische Agenten-Profile entstehen. Stufe 3 orchestriert
schliesslich komplexe Geschäftsprozesse, in denen Agenten, Menschen und bestehende Systeme (wie SAP oder SharePoint)
nahtlos zusammenarbeiten. Dieser Ansatz stellt sicher, dass die technologische Komplexität stets im Einklang mit dem
fachlichen Nutzen wächst.

### Technische Umsetzung im Swiss AI Hub

Die Plattform ist für ein Ein-Befehl-Deployment optimiert. Mittels Docker oder Kubernetes wird der gesamte Stack
inklusive Datenbanken, Message Queues und Benutzeroberflächen in wenigen Minuten bereitgestellt. Die Trennung von
Plattform und SDK erlaubt es Entwicklern, sich ausschliesslich auf die Geschäftslogik der Agenten-Baupläne zu
konzentrieren, während die Plattform Funktionen wie Authentifizierung via SSO/OAuth, Kostenmanagement pro Team und
automatische Datenpipelines mittels Dagster und Docling übernimmt.

## Vertrauen durch Transparenz und Closed Workflows

### Geschäftlicher Nutzen

Ein zentrales Hemmnis für KI im Unternehmen ist die mangelnde Vorhersehbarkeit autonomer Systeme. Entscheidungsträger
benötigen die Gewissheit, dass KI-Systeme definierte Prozesse einhalten und dass jede Entscheidung nachvollziehbar
bleibt. Der Swiss AI Hub schafft dieses Vertrauen, indem er Zufall durch deterministische Abläufe ersetzt. Dies ist
essenziell für interne Audits, die Akzeptanz bei den Mitarbeitenden und die Erfüllung regulatorischer Anforderungen wie
dem EU AI Act.

### Konzeptioneller Ansatz

Anstatt offenen Agentenschleifen freien Lauf zu lassen, setzt der Swiss AI Hub auf Workflow-basierte Agenten in
sogenannten «Closed Workflows». Ein Agenten-Bauplan definiert exakte Schritte und Pfade. Ein Agent kann keine
unvorhersehbaren Aktionen ausführen oder auf Daten zugreifen, die nicht explizit für sein Agenten-Profil freigegeben
wurden. Ergänzt wird dies durch das Prinzip der vollständigen Observability, bei dem jede Interaktion protokolliert und
visualisiert wird.

### Technische Umsetzung im Swiss AI Hub

Die Nachvollziehbarkeit wird technisch durch die Integration von Phoenix für Tracing und Evaluation sichergestellt.
Jeder Schritt eines Agenten erzeugt Trace-Daten, die genau aufzeigen, welche Dokumente aus der Wissensdatenbank
herangezogen wurden und wie das Modell zur Antwort kam. Administratoren können über Dashboards in Echtzeit verfolgen,
wie Agenten agieren, Kosten überwachen und bei Bedarf menschliche Genehmigungsschritte (Human-in-the-Loop) in die
Prozesse integrieren.

## Investitionsschutz durch Open Source und Unabhängigkeit

### Geschäftlicher Nutzen

In einem sich rasant wandelnden Technologiemarkt ist die Abhängigkeit von einem einzelnen Anbieter ein erhebliches
strategisches Risiko. Proprietäre Plattformen binden Kunden oft durch intransparente Preismodelle. Der Swiss AI Hub
bietet hierzu einen Gegenentwurf: Als Open-Source-Plattform unter der Apache 2.0 Lizenz garantiert er maximale
Unabhängigkeit. Unternehmen investieren in ihre eigene Infrastruktur, was die langfristige Portierbarkeit und
Prüfbarkeit des Systems sichert.

### Konzeptioneller Ansatz

Das System ist konsequent modell-agnostisch gestaltet. Es abstrahiert die darunterliegenden Sprachmodelle über das
LLM-Gateway. Unternehmen können heute ein globales Modell nutzen und morgen nahtlos auf ein kosteneffizienteres oder ein
lokales Modell wechseln, ohne ihre Agenten-Baupläne anpassen zu müssen. Dieser Ansatz stärkt die Verhandlungsposition
gegenüber Providern und schützt die getätigten Entwicklungs-Investitionen.

### Technische Umsetzung im Swiss AI Hub

Die technische Basis bildet ein moderner Technologie-Stack (PostgreSQL, Valkey, NATS), der in der Industrie weit
verbreitet ist. Das LLM-Gateway (LiteLLM) vereinheitlicht die APIs verschiedener Provider. Da der Quellcode offenliegt,
können interne IT-Teams die Plattform jederzeit auditieren oder erweitern. Die Datenhaltung erfolgt in offenen Formaten,
was den Export und die Migration von Daten sowie des gesammelten Wissens in der Wissensdatenbank jederzeit ermöglicht.
