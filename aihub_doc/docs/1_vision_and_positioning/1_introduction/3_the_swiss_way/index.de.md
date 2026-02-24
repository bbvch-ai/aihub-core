---
title: Der Schweizer Weg
source_sha: ea077dd40223dce7e36a70320ea9c5725048b359ceff49089b66c0a3bed35085
---

# Der Schweizer Weg: Datenschutz, Souveränität und Transparenz

Der Swiss AI Hub verkörpert Schweizer Werte, aber nicht als Marketing-Schlagworte. Diese Prinzipien existieren aus einem
Grund: Vertrauen aufzubauen. Schweizer Organisationen übernehmen Technologien nicht leichtfertig, insbesondere wenn es
um ihre Daten und Tools geht. Diese Vorsicht ist gerechtfertigt – KI-Demonstrationen sind beeindruckend, aber
Produktions-KI muss Vertrauen durch Transparenz, Kontrolle und Vorhersehbarkeit verdienen.

## Vertrauen durch eingegrenztes Verhalten

Die meisten KI-Plattformen verwenden offene Agents: Geben Sie ihnen Tools und ein Ziel, lassen Sie sie den Rest selbst
herausfinden. Dieser Ansatz funktioniert in Demos, erzeugt aber in der Produktion Bedenken. Woher wissen Sie, dass der
Agent nichts Unerwartetes tun wird? Wie prüfen Sie seine Entscheidungen? Wie erklären Sie seine Fehler?

Der Swiss AI Hub verfolgt einen anderen Ansatz:

**Geschlossene Workflows statt offener Schleifen**\
Unsere Agents folgen expliziten, schrittweisen Workflows. Jeder Schritt definiert, was geschehen kann, wohin Daten
fließen und welche Entscheidungen möglich sind. Ein Agent kann nicht plötzlich entscheiden, auf Daten zuzugreifen, die
er nicht sollte, oder Aktionen auszuführen, die Sie nicht erwartet haben – er kann nur die von Ihnen definierten
Workflow-Schritte ausführen.

**Beobachtbar auf jeder Ebene**\
Vertrauen erfordert Sichtbarkeit. Die Plattform bietet vier Ebenen der Observability:

- **Infrastruktur-Monitoring** durch OpenTelemetry und Signoz verfolgt die Ressourcennutzung und API-Performance
- **Agent-Ausführungs-Tracing** durch OpenInference und Langfuse zeigt jeden LLM-Aufruf und jede Entscheidung
- **Workflow-Event-Streams** machen jeden Schritt im Prozess des Agenten sichtbar und debugfähig
- **Pipeline-Observability** durch Dagster zeigt genau, wie Ihre Daten verarbeitet werden und wohin sie gehen

**Messbare Performance**\
Hoffnung ist keine Strategie. Die Plattform enthält Bewertungs-Frameworks, die die Genauigkeit von Agents anhand von
Testdatensätzen messen. Sie müssen nicht darauf vertrauen, dass Agents korrekt funktionieren – Sie können es mit
Metriken beweisen.

## Vertrauen durch Datensouveränität

::: warning Ihre Daten, Ihre Infrastruktur
Datensouveränität ist nicht nur Compliance – es geht um Kontrolle. Wenn Sie den Swiss AI Hub deployen, verlassen Ihre
Daten niemals Ihre Infrastruktur, es sei denn, Sie konfigurieren dies explizit. Betreiben Sie alles On-Premise mit
lokalen LLMs, und Ihre sensiblen Daten überschreiten niemals Ihre Netzwerkgrenze.
:::

Dies ist keine theoretische Fähigkeit. Die Plattform wird mit Konfigurationen für Folgendes ausgeliefert:

- **Vollständig On-Premise Deployment** mit Open-Source-Modellen wie Mistral oder DeepSeek
- **Swiss Cloud Deployment** unter ausschließlicher Nutzung Schweizer Rechenzentren
- **Hybrid Deployment**, das sensible Daten lokal hält, während die Cloud für nicht-kritische Workloads genutzt wird

Sie wählen, wo jede Komponente läuft, wo Daten gespeichert werden und welche Modelle welche Informationen verarbeiten.
Diese granulare Kontrolle bedeutet, dass Sie mit maximaler Sicherheit beginnen und die Einschränkungen schrittweise
lockern können, wenn sich Vertrauen aufbaut.

## Vertrauen durch Transparenz

Die Transparenz der Plattform geht über Open Source hinaus:

**Prüfbare Entscheidungen**\
Jede Agent-Entscheidung wird mit vollständigem Kontext protokolliert. Nicht nur, was entschieden wurde, sondern auch
warum – welche Daten berücksichtigt wurden, welche Regeln angewendet wurden, welche Konfidenzniveaus berechnet wurden.
Compliance-Teams können jede Ausgabe bis zu ihren Quellen zurückverfolgen.

**Erklärbare Workflows**\
Da Agents definierten Workflows folgen, können Sie ihr Verhalten nicht-technischen Stakeholdern erklären. „Der Agent
analysiert das Dokument, extrahiert Schlüsselinformationen, gleicht sie mit unseren Regeln ab und fordert dann die
menschliche Genehmigung an“ – nicht „die KI führt eine Verarbeitung durch“.

**Sichtbare Integrationen**\
Wenn die Plattform sich mit externen Systemen verbindet, sind diese Verbindungen explizit und werden überwacht. Sie
sehen, welche Daten zu welchen Services fließen, welche Antworten zurückkommen und wie sie verarbeitet werden.

## Vertrauen durch schrittweise Einführung

Schweizer Organisationen führen keine „Big Bang“-Transformationen durch, und die Plattform respektiert dies:

**Beginnen Sie mit schreibgeschütztem Zugriff**\
Beginnen Sie mit Agents, die nur Informationen abrufen und analysieren. Keine Schreibberechtigungen, keine
Systemmodifikationen, keine automatisierten Entscheidungen. Bauen Sie Vertrauen durch sichere Operationen auf.

**Erweitern Sie mit menschlicher Aufsicht**\
Fügen Sie Funktionen schrittweise hinzu, immer mit menschlichen Genehmigungsschritten. Der Agent bereitet die Arbeit
vor; Menschen verifizieren und führen aus. Wenn das Vertrauen wächst, reduzieren Sie die Aufsicht, wo angemessen.

**Isolation nach Kritikalität**\
Betreiben Sie separate Instanzen für unterschiedliche Sicherheitsstufen. Testen Sie neue Funktionen in der Entwicklung,
validieren Sie sie im Staging und deployen Sie sie nur in die Produktion, wenn sie sich bewährt haben. Kritische Systeme
können isoliert bleiben, während weniger sensible tiefer integriert werden.

## Vertrauen durch professionelle Ingenieurskunst

Die Plattform ist kein Forschungsprojekt oder MVP eines Startups. Sie wird nach Schweizer Ingenieurstandards gebaut:

- **Umfassende Tests** auf Unit-, Integrations- und Systemebene
- **Type Safety**, die im gesamten Codebase durchgesetzt wird
- **Fehlerbehandlung**, die anmutig herabstuft, anstatt katastrophal zu versagen
- **Security by Design** mit integrierter Authentifizierung, Autorisierung und Verschlüsselung
- **Professionelle Dokumentation**, die nicht nur das Wie, sondern auch das Warum erklärt

## Die Vertrauensgleichung

Vertrauen in KI resultiert aus einer einfachen Gleichung:

**Vorhersehbarkeit + Sichtbarkeit + Kontrolle = Vertrauen**

- **Vorhersehbarkeit** durch eingegrenzte Workflows und definiertes Verhalten
- **Sichtbarkeit** durch umfassende Observability und Audit-Trails
- **Kontrolle** durch Datensouveränität und Konfigurationsoptionen

Der Swiss AI Hub bietet alle drei. Nicht durch Versprechen oder proprietäre Black Boxes, sondern durch offene,
inspizierbare, modifizierbare Infrastruktur, die Sie besitzen und betreiben.

Das ist der Schweizer Weg: Vertrauen durch Transparenz verdienen, Vertrauen durch Zuverlässigkeit erhalten und Vertrauen
durch den Respekt vor Ihren Daten, Ihren Prozessen und Ihrer Vorsicht verdienen. Denn in der Schweiz wird Vertrauen
nicht einfach gegeben – es wird durch Demonstration verdient, durch Beständigkeit aufrechterhalten und über schnelle
Adoption gestellt.
