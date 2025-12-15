# Executive Summary

Der Swiss AI Hub löst das zentrale Dilemma, dem sich Schweizer Unternehmen bei der Einführung künstlicher Intelligenz
gegenübersehen: Wie lassen sich die Vorteile moderner Sprachmodelle nutzen, ohne die Kontrolle über sensible Daten an
ausländische Cloud-Anbieter abzugeben oder Jahre an Entwicklungszeit in den Aufbau eigener Infrastruktur zu investieren?

Dieses Whitepaper richtet sich an Entscheidungsträger, die eine produktionsreife, souveräne und zukunftssichere
KI-Plattform suchen. Es legt dar, warum der Swiss AI Hub nicht nur ein weiteres Entwicklungswerkzeug ist, sondern eine
vollständige Enterprise-KI-Infrastruktur, die Sie besitzen, kontrollieren und innerhalb kürzester Zeit in Betrieb nehmen
können. Wir schliessen die Lücke zwischen einem funktionierenden Prototyp und einem sicheren, skalierbaren
Produktionssystem.

## Auf einen Blick

- **Vollständige Infrastruktur statt Baukasten:** Eine produktionsreife Plattform, die «Day 2»-Probleme wie
  Authentifizierung, Kostenkontrolle und Monitoring bereits im Standard löst.
- **Garantierte Schweizer Datensouveränität:** Die Daten verlassen niemals Ihren Sicherheitsperimeter, es sei denn, Sie
  konfigurieren es explizit.
- **Kein Vendor Lock-in:** Dank Open-Source-Architektur (Apache 2.0) und Modell-Agnostik bleiben Sie unabhängig von
  spezifischen KI-Anbietern.
- **Vertrauen durch «Closed Workflows»:** Deterministische Agenten-Abläufe statt unvorhersehbarer
  Black-Box-Entscheidungen sorgen für Compliance und Sicherheit.

## Strategische Datensouveränität und Compliance

### Geschäftlicher Nutzen

Für Schweizer Organisationen, insbesondere in regulierten Sektoren wie Finanzwesen, Gesundheit oder Verwaltung, ist der
Einsatz öffentlicher KI-Dienste oft mit untragbaren Risiken verbunden. Das Hochladen vertraulicher Unternehmensdaten in
die Cloud globaler Hyperscaler kollidiert häufig mit internen Richtlinien oder gesetzlichen Vorgaben. Dies führt dazu,
dass Innovationsprojekte blockiert werden oder in einer rechtlichen Grauzone stattfinden. Der Swiss AI Hub löst diesen
Konflikt, indem er vollständige Datensouveränität garantiert. Unternehmen müssen sich nicht länger zwischen
technologischer Innovation und Compliance entscheiden; sie erhalten die Fähigkeit, modernste KI-Modelle zu nutzen,
während die Datenhoheit uneingeschränkt im eigenen Unternehmen verbleibt.

### Konzeptioneller Ansatz

Das zugrundeliegende Prinzip ist die absolute Kontrolle über den Speicherort und den Fluss der Daten. Im Gegensatz zu
SaaS-Lösungen, bei denen Daten extern verarbeitet werden, ist der Swiss AI Hub als Infrastruktur konzipiert, die der
Kunde selbst betreibt (Self-Hosted). Ob On-Premise auf eigenen Servern, in einer privaten Schweizer Cloud oder in einer
abgeschotteten Umgebung: Die Daten verlassen niemals den vom Mandanten definierten Sicherheitsperimeter. Dieses Konzept
ermöglicht auch den Einsatz von lokalen Open-Source-Modellen für hochsensible Daten (PII), während weniger kritische
Anfragen bei Bedarf an externe Anbieter geleitet werden können.

### Technische Umsetzung im Swiss AI Hub

Technisch realisiert der Swiss AI Hub dies durch eine containerisierte Architektur, die vollständig auf der
Infrastruktur des Mandanten läuft. Kernkomponenten wie die Vektordatenbank (implementiert durch Milvus) für die
Speicherung von Unternehmenswissen und die Daten-zu-Wissen-Pipeline operieren lokal. Zudem integriert die Plattform
«Presidio» zur automatischen Erkennung und Anonymisierung von Personenidentifizierbaren Informationen (PII), bevor diese
überhaupt an ein Modell gesendet werden. Das integrierte LLM-Gateway (LiteLLM) fungiert als zentrale Schleuse, die den
Datenfluss zu den Modellen steuert und überwacht.

## Von der Demo zur Produktion: Der «Day 2»-Vorteil

### Geschäftlicher Nutzen

Viele KI-Initiativen scheitern nach der ersten Euphorie. Ein Prototyp ist schnell erstellt, doch der Schritt in den
produktiven Betrieb – der sogenannte «Day 2» – offenbart massive Lücken: fehlende Benutzerverwaltung, unklare
Kostenstrukturen, Sicherheitsrisiken und mangelnde Integration in bestehende Systeme. Unternehmen unterschätzen oft,
dass sie für einen sicheren Betrieb nicht nur KI-Logik, sondern komplexe Infrastruktur entwickeln müssen. Der Swiss AI
Hub eliminiert diesen Aufwand, indem er diese «Day 2»-Probleme bereits im Standard löst. Dies verkürzt die Time-to-Value
drastisch und reduziert Investitionsrisiken.

### Konzeptioneller Ansatz

Der Swiss AI Hub versteht sich als «Infrastruktur als Produkt». Anstatt nur Bibliotheken oder Frameworks
bereitzustellen, liefert die Plattform alle notwendigen Enterprise-Komponenten fixfertig integriert aus. Das Konzept
basiert auf der strikten Trennung von Plattform und SDK: Die Plattform stellt Funktionen wie Authentifizierung,
Monitoring, Datenbanken und Messaging bereit, während sich die Entwickler über das SDK ausschliesslich auf die
Geschäftslogik der Agenten konzentrieren. Dies verhindert die Entstehung von isolierten KI-Silos und fragmentierten
Tool-Landschaften im Unternehmen.

### Technische Umsetzung im Swiss AI Hub

Die Plattform bietet out-of-the-box eine Integration in bestehende Identity Provider via SSO/OAuth. Das zentrale
LLM-Gateway bietet ein granulares Kostenmanagement, mit dem Budgets pro Benutzer oder Team überwacht werden. Für die
Datenverarbeitung werden robuste Pipelines mittels Dagster eingesetzt, während Docling das Parsing komplexer Dokumente
übernimmt. Die Kommunikation der Komponenten erfolgt ereignisgesteuert über NATS. Diese vorintegrierten
Best-of-Breed-Komponenten ermöglichen ein Deployment des gesamten Stacks via Docker oder Kubernetes in wenigen Minuten.

## Vertrauen durch Transparenz und «Closed Workflows»

### Geschäftlicher Nutzen

Ein zentrales Hemmnis für KI im Unternehmen ist die mangelnde Vorhersehbarkeit. Autonome Agenten, die als «Black Box»
agieren, stellen ein unkalkulierbares Risiko dar. Entscheidungsträger benötigen die Gewissheit, dass KI-Systeme
definierte Prozesse einhalten und Entscheidungen nachvollziehbar sind. Der Swiss AI Hub schafft dieses Vertrauen, indem
er Zufall durch deterministische Abläufe ersetzt und vollständige Transparenz über jede Aktion bietet. Dies ist
essenziell für Audits und die interne Akzeptanz.

### Konzeptioneller Ansatz

Anstatt offenen Agentenschleifen freien Lauf zu lassen, setzt der Swiss AI Hub auf «Closed Workflows». Ein
Agenten-Bauplan definiert exakte Schritte und Pfade, denen der Agent folgen muss. Es gibt keine unvorhersehbaren
Abzweigungen. Ergänzt wird dies durch das Prinzip der vollständigen Observability: Jede Entscheidung, jeder Datenzugriff
und jeder Modellaufruf wird protokolliert und ist visualisierbar. Dies ermöglicht eine lückenlose «Chain of
Thought»-Analyse.

### Technische Umsetzung im Swiss AI Hub

Die Nachvollziehbarkeit wird technisch durch die Integration von Phoenix für Tracing und Evaluation sichergestellt.
Jeder Schritt eines Workflow-basierten Agenten erzeugt Trace-Daten, die genau aufzeigen, welche Dokumente aus der
Wissensdatenbank (Retrieval-Augmented Generation) herangezogen wurden und wie das Modell zur Antwort kam.
Administratoren können über Dashboards in Echtzeit verfolgen, was die Agenten tun, und bei Bedarf eingreifen.

## Investitionsschutz durch Open Source und Unabhängigkeit

### Geschäftlicher Nutzen

In einem sich rasant wandelnden Markt ist die Abhängigkeit von einem einzelnen Anbieter (Vendor Lock-in) ein erhebliches
strategisches Risiko. Proprietäre Plattformen binden Kunden oft durch intransparente Preismodelle und geschlossene
Ökosysteme. Der Swiss AI Hub bietet hierzu einen Gegenentwurf: Als Open-Source-Plattform unter der Apache 2.0 Lizenz
garantiert er maximale Unabhängigkeit. Unternehmen investieren in ihre eigene Infrastruktur, nicht in Mietsoftware. Dies
sichert langfristig die Investition, da der Code jederzeit prüfbar, anpassbar und portierbar bleibt.

### Konzeptioneller Ansatz

Das System ist darauf ausgelegt, «modell-agnostisch» zu sein. Es zwingt den Mandanten nicht in das Ökosystem eines
spezifischen KI-Herstellers. Stattdessen abstrahiert die Plattform die darunterliegenden KI-Modelle. Unternehmen können
heute GPT-4 nutzen und morgen nahtlos auf ein kosteneffizienteres Modell wie Claude 3 oder ein lokales Modell wie
Mistral wechseln, ohne ihre Agenten-Baupläne umschreiben zu müssen. Dieser Ansatz stärkt die Verhandlungsposition
gegenüber Modell-Anbietern.

### Technische Umsetzung im Swiss AI Hub

Die technische Basis bildet ein moderner, quelloffener Technologie-Stack (Docker, Python, PostgreSQL, ValKey), der in
der Industrie weit verbreitet ist. Das LLM-Gateway abstrahiert die APIs verschiedener Provider, sodass der Wechsel eines
Modells oft nur eine Konfigurationsänderung ist. Die Datenhaltung erfolgt in offenen Formaten, was den Export und die
Migration von Daten jederzeit ermöglicht. Da der Quellcode offenliegt, können interne IT-Teams die Plattform bei Bedarf
auditieren oder erweitern.
