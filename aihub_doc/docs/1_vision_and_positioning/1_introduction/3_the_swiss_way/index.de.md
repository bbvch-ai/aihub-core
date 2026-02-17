---
title: Der Schweizer Weg
source_sha: 3f28644254bb0df397297f79307abd4e82b005bb29265a8769d21dad7221755c
---

# Der Schweizer Weg: Privatsphäre, Souveränität und Transparenz

Der Swiss AI Hub verkörpert Schweizer Werte, jedoch nicht als Marketing-Schlagworte. Diese Prinzipien existieren aus
einem Grund: Vertrauen aufzubauen. Schweizer Organisationen übernehmen Technologie nicht leichtfertig, besonders wenn es
um ihre Daten und Tools geht. Diese Vorsicht ist gerechtfertigt – KI-Demonstrationen sind beeindruckend, doch KI im
Produktivbetrieb muss Vertrauen durch Transparenz, Kontrolle und Vorhersagbarkeit gewinnen.

## Vertrauen durch begrenztes Verhalten

Die meisten KI-Plattformen nutzen offene Agenten: Man gibt ihnen Tools und ein Ziel, den Rest sollen sie selbst
herausfinden. Dieser Ansatz funktioniert in Demos, erzeugt aber im Produktivbetrieb Unsicherheit. Woher wissen Sie, dass
der Agent nichts Unerwartetes tun wird? Wie prüfen Sie seine Entscheidungen? Wie erklären Sie seine Fehler?

Der Swiss AI Hub verfolgt einen anderen Ansatz:

**Geschlossene Workflows statt offener Schleifen**\
Unsere Agenten folgen expliziten, schrittweisen Workflows. Jeder Schritt definiert, was geschehen kann, welche Daten
wohin fließen und welche Entscheidungen möglich sind. Ein Agent kann nicht plötzlich entscheiden, auf Daten zuzugreifen,
die er nicht sollte, oder Aktionen auszuführen, die Sie nicht erwartet haben – er kann nur die von Ihnen definierten
Workflow-Schritte ausführen.

**Auf jeder Ebene beobachtbar**\
Vertrauen erfordert Sichtbarkeit. Die Plattform bietet vier Ebenen der Beobachtbarkeit:

- **Infrastruktur-Monitoring** über OpenTelemetry und Signoz verfolgt Ressourcennutzung und API-Performance
- **Agenten-Ausführungsverfolgung** über OpenInference und Phoenix zeigt jeden LLM-Aufruf und jede Entscheidung
- **Workflow-Event-Streams** machen jeden Schritt im Prozess des Agenten sichtbar und debugbar
- **Pipeline-Beobachtbarkeit** über Dagster zeigt genau, wie Ihre Daten verarbeitet werden und wohin sie gelangen

**Messbare Leistung**\
Hoffnung ist keine Strategie. Die Plattform enthält Bewertungs-Frameworks, die die Genauigkeit von Agenten anhand von
Testdatensätzen messen. Sie müssen nicht darauf vertrauen, dass Agenten korrekt funktionieren – Sie können es mit
Metriken beweisen.

## Vertrauen durch Datenhoheit

::: warning Ihre Daten, Ihre Infrastruktur
Datenhoheit ist nicht nur eine Frage der Compliance – es geht um Kontrolle. Wenn Sie den Swiss AI Hub bereitstellen,
verlassen Ihre Daten niemals Ihre Infrastruktur, es sei denn, Sie konfigurieren dies explizit. Betreiben Sie alles
On-Premise mit lokalen LLMs, und Ihre sensiblen Daten überschreiten niemals Ihre Netzwerkgrenzen.
:::

Dies ist keine theoretische Fähigkeit. Die Plattform wird mit Konfigurationen ausgeliefert für:

- **Vollständige On-Premise-Bereitstellung** mit Open-Source-Modellen wie Mistral oder DeepSeek
- **Schweizer Cloud-Bereitstellung** unter ausschließlicher Nutzung Schweizer Rechenzentren
- **Hybride Bereitstellung**, bei der sensible Daten lokal bleiben, während die Cloud für nicht-kritische Workloads
  genutzt wird

Sie wählen, wo jede Komponente läuft, wo Daten gespeichert werden und welche Modelle welche Informationen verarbeiten.
Diese granulare Kontrolle bedeutet, dass Sie mit maximaler Sicherheit beginnen und Einschränkungen schrittweise lockern
können, wenn das Vertrauen wächst.

## Vertrauen durch Transparenz

Die Transparenz der Plattform geht über Open Source hinaus:

**Prüfbare Entscheidungen**\
Jede Agentenentscheidung wird mit vollem Kontext protokolliert. Nicht nur, was entschieden wurde, sondern auch warum –
welche Daten berücksichtigt, welche Regeln angewendet, welche Konfidenzlevel berechnet wurden. Compliance-Teams können
jede Ausgabe bis zu ihren Quellen zurückverfolgen.

**Erklärbare Workflows**\
Da Agenten definierten Workflows folgen, können Sie ihr Verhalten auch nicht-technischen Stakeholdern erklären. „Der
Agent analysiert das Dokument, extrahiert Schlüsselinformationen, gleicht sie mit unseren Regeln ab und fordert dann die
Genehmigung durch einen Menschen an“ – nicht „die KI führt eine Verarbeitung durch.“

**Sichtbare Integrationen**\
Wenn die Plattform sich mit externen Systemen verbindet, sind diese Verbindungen explizit und werden überwacht. Sie
sehen, welche Daten an welche Dienste fließen, welche Antworten zurückkommen und wie sie verarbeitet werden.

## Vertrauen durch schrittweise Einführung

Schweizer Organisationen führen keine „Big-Bang“-Transformationen durch, und die Plattform respektiert dies:

**Beginnen Sie mit schreibgeschütztem Zugriff**\
Beginnen Sie mit Agenten, die nur Informationen abrufen und analysieren. Keine Schreibberechtigungen, keine
Systemmodifikationen, keine automatisierten Entscheidungen. Bauen Sie Vertrauen durch sichere Operationen auf.

**Erweitern Sie mit menschlicher Aufsicht**\
Fügen Sie Funktionen schrittweise hinzu, immer mit menschlichen Genehmigungsschritten. Der Agent bereitet die Arbeit
vor; Menschen überprüfen und führen aus. Wenn das Vertrauen wächst, reduzieren Sie die Aufsicht gegebenenfalls.

**Isolation nach Kritikalität**\
Betreiben Sie separate Instanzen für verschiedene Sicherheitsstufen. Testen Sie neue Funktionen in der Entwicklung,
validieren Sie im Staging, und stellen Sie nur dann in der Produktion bereit, wenn sie sich bewährt haben. Kritische
Systeme können isoliert bleiben, während weniger sensible tiefer integriert werden.

## Vertrauen durch professionelle Entwicklung

Die Plattform ist kein Forschungsprojekt oder MVP eines Startups. Sie wurde nach Schweizer Ingenieursstandards
entwickelt:

- **Umfassende Tests** auf Unit-, Integrations- und Systemebene
- **Typensicherheit**, die im gesamten Code durchgesetzt wird
- **Fehlerbehandlung**, die sich elegant herabstuft, anstatt katastrophal zu versagen
- **Security by Design** mit integrierter Authentifizierung, Autorisierung und Verschlüsselung
- **Professionelle Dokumentation**, die nicht nur das Wie, sondern auch das Warum erklärt

## Die Vertrauensgleichung

Vertrauen in KI ergibt sich aus einer einfachen Gleichung:

**Vorhersagbarkeit + Sichtbarkeit + Kontrolle = Vertrauen**

- **Vorhersagbarkeit** durch begrenzte Workflows und definierte Verhaltensweisen
- **Sichtbarkeit** durch umfassende Beobachtbarkeit und Audit-Trails
- **Kontrolle** durch Datenhoheit und Konfigurationsoptionen

Der Swiss AI Hub bietet alle drei. Nicht durch Versprechen oder proprietäre Black Boxes, sondern durch eine offene,
überprüfbare, modifizierbare Infrastruktur, die Sie besitzen und betreiben.

Das ist der Schweizer Weg: Vertrauen durch Transparenz verdienen, Vertrauen durch Zuverlässigkeit aufrechterhalten und
Vertrauen durch Respekt für Ihre Daten, Ihre Prozesse und Ihre Vorsicht verdienen. Denn in der Schweiz wird Vertrauen
nicht geschenkt – es wird durch Demonstration erworben, durch Konsistenz bewahrt und über eine schnelle Einführung
gestellt.
