---
title: Wissensorganisation durch Namespaces
source_sha: 8737934ea649e19970c0de1c1c3e3e9ce525096ad8474319857d5dfc394fe4a6
---

# Wissensorganisation durch Namespaces

Der Swiss AI-Hub organisiert Unternehmenswissen mittels einer Namespace-basierten Architektur, die logische Trennung,
flexible Zugriffskontrolle und unabhängiges Lifecycle-Management für verschiedene Wissensbereiche bietet. Dieser Ansatz
ermöglicht Organisationen, ihre Wissensdatenbanken so zu strukturieren, dass sie die Geschäftsrealität widerspiegeln und
gleichzeitig die Abrufperformance und das operative Management optimieren.

## Das Namespace-Konzept

Namespaces fungieren als logische Container für zusammengehörige Dokumente und Informationen, ähnlich wie Ordner in
einem Dateisystem, aber optimiert für die Vektor-Ähnlichkeitssuche. Jeder Namespace repräsentiert einen eigenen
Wissensbereich – eine Produktlinie, Geschäftseinheit, einen regulatorischen Rahmen oder eine andere logische
Gruppierung, die für die Organisation von Bedeutung ist. Dokumente, die in den Vektor-Store aufgenommen werden, erhalten
Namespace-Zuweisungen als Metadaten, was ein präzises Targeting bei Abrufoperationen ermöglicht.

Im Gegensatz zu traditionellen Ordnerhierarchien existieren Namespaces als flache Metadatenattribute, die an jeden
Dokumenten-Chunk im Vektor-Store angehängt sind. Diese flache Struktur ermöglicht es Agenten, gleichzeitig in mehreren
Namespaces zu suchen, ohne hierarchische Pfade navigieren zu müssen, wodurch die organisatorischen Vorteile der
Kategorisierung mit den Performance-Vorteilen der direkten Metadatenfilterung kombiniert werden.

## Zugriffskontrolle auf Agenten-Ebene

Die Plattform implementiert eine Namespace-Zugriffskontrolle auf Agenten-Ebene: Wenn ein Agent für den Zugriff auf
bestimmte Namespaces konfiguriert ist, **erhalten alle Benutzer, die mit diesem Agenten interagieren, Antworten, die auf
demselben Wissensset basieren**. Dies gewährleistet ein konsistentes, vorhersehbares Agentenverhalten und vereinfacht
Tests und Validierungen.

**Zugriffsphilosophie**: Agenten sind aufgabenorientierte Tools, die mit dem Wissen konfiguriert werden, das für ihre
vorgesehene Funktion erforderlich ist. Die Zugriffskontrolle erfolgt auf Agenten-Ebene – wenn Benutzer keine
Informationen innerhalb der Namespaces eines Agenten abrufen dürfen, sollten sie keine Berechtigung zur Nutzung dieses
Agenten erhalten.

**Agenten-Wiederverwendbarkeit**: Derselbe Agenten-Workflow kann mehrfach mit unterschiedlichen
Namespace-Konfigurationen instanziiert werden, wodurch unterschiedliche Instanzen für verschiedene Zielgruppen
entstehen. Zum Beispiel könnte ein Support-Agenten-Workflow wie folgt bereitgestellt werden:

- **Öffentlicher Support-Agent**: Nur öffentliche Dokumentation, für alle Kunden verfügbar
- **Partner-Support-Agent**: Öffentliche und partnerspezifische Namespaces, für autorisierte Partner
- **Interner Support-Agent**: Voller Zugriff, einschließlich interner technischer Dokumentation, nur für Mitarbeiter

Jede Instanz verwendet identische Workflow-Logik, operiert jedoch auf unterschiedlichen Wissensbereichen, wodurch ein
angemessener Informationszugriff ohne komplexe Filterung pro Benutzer gewährleistet wird.

**Optionale Benutzervalidierung**: Organisationen können optional überprüfen, ob Benutzer über Berechtigungen für alle
Namespaces verfügen, auf die ein Agent zugreift. Wenn aktiviert, prüft die Plattform die Benutzerberechtigungen vor der
Workflow-Ausführung – Benutzer erhalten entweder volle Agenten-Funktionalität oder eine klare Ablehnung, niemals
Teilergebnisse.

## Wissenszugriffsmuster

**Domänenspezialisierung**: Spezialisierte Agenten konzentrieren sich auf bestimmte Wissensbereiche, indem sie den
Namespace-Zugriff einschränken. Ein Agent für die Einhaltung gesetzlicher Vorschriften könnte nur auf rechtliche und
Compliance-Namespaces zugreifen, während ein Produktsupport-Agent auf technische Dokumentation zugreift. Diese
Spezialisierung verbessert die Abrufrelevanz, indem sie eine Kontamination durch irrelevante Informationen verhindert.

**Multi-Domänen-Agenten**: Agenten, die umfassenderes Wissen benötigen, spezifizieren mehrere Namespaces in ihrer
Abrufkonfiguration. Die Plattform führt den Abruf parallel über alle konfigurierten Namespaces durch und führt die
Ergebnisse nach Relevanz-Scores zusammen, um die relevantesten Informationen unabhängig vom Namespace-Ursprung zu
präsentieren.

**Dynamische Bereichsanpassung**: Organisationen ändern den Namespace-Zugriff von Agenten durch
Konfigurationsaktualisierungen ohne Codeänderungen. Das Hinzufügen einer neuen Produktlinie erfordert lediglich die
Aktualisierung der Agentenkonfigurationen, um den neuen Namespace aufzunehmen, wodurch dieses Wissen sofort verfügbar
gemacht wird.

## Betriebliche Vorteile

**Unabhängige Updates**: Organisationen können Wissen in einem Namespace aktualisieren, ohne andere zu beeinflussen. Das
Testen neuer Ingestion-Pipelines kann in isolierten Namespaces erfolgen, ohne die Produktionsagenten, die auf
etablierten Namespaces operieren, zu beeinträchtigen.

**Zugriffskontrolle durch Bereitstellung**: Organisationen stellen mehrere Agenten-Instanzen mit unterschiedlichen
Namespace-Konfigurationen bereit und steuern, welche Benutzer auf welche Agenten zugreifen. Mitarbeiter mit
entsprechenden Freigaben greifen auf Agenten zu, die mit vertraulichen Namespaces konfiguriert sind, während
Auftragnehmer auf separate Instanzen zugreifen, die nur öffentlich teilbare Namespaces enthalten.

**Leistungsoptimierung**: Die Einschränkung des Abrufs auf relevante Namespaces reduziert den Suchraum und verbessert
sowohl die Geschwindigkeit als auch die Relevanz. Wenn Wissensdatenbanken wachsen, verhindert der Namespace-fokussierte
Abruf eine Leistungsdegradation – Agenten behalten eine konsistente Leistung, unabhängig von der Gesamtgröße der
Wissensdatenbank.

**Lifecycle-Management**: Verschiedene Namespaces folgen unterschiedlichen Aufbewahrungsrichtlinien und
Aktualisierungszyklen. Rechtliche Dokumente erfordern eine lange Aufbewahrung mit seltenen Aktualisierungen, während
Produktspezifikationen häufig aktualisiert werden, aber nach der Einstellung verfallen. Organisationen können inaktive
Namespaces archivieren, ohne aktuelle Agenten zu beeinflussen.

## Design-Überlegungen

Ein effektives Namespace-Design berücksichtigt mehrere Faktoren:

**Granularität**: Namespaces definieren die feinste Granularität der Zugriffskontrolle. Die meisten Organisationen
finden eine optimale Granularität auf Ebene der Geschäftseinheit, Produktfamilie oder des Funktionsbereichs – grob
genug, um eine übermäßige Agentenproliferation zu vermeiden, fein genug, um eine sinnvolle Zugriffs-Differenzierung zu
ermöglichen.

**Stabilität**: Namespace-Strukturen sollten über die Zeit relativ stabil bleiben, da Reorganisationen ein erneutes
Einpflegen und eine Neukonfiguration der Agenten erfordern. Entwerfen Sie Schemata, die Geschäftswachstum ohne häufige
Umstrukturierungen berücksichtigen.

**Auffindbarkeit**: Klare Benennungskonventionen und Dokumentationen helfen Administratoren zu verstehen, welche
Namespaces relevantes Wissen für bestimmte Agenten-Rollen bereitstellen und welche Kombinationen angemessene
Zugriffsbereiche ermöglichen.

**Übergreifende Bedenken**: Informationen, die mehrere Domänen betreffen (Sicherheitsrichtlinien, Markenrichtlinien),
können in mehreren Namespaces dupliziert oder in dedizierten, übergreifenden Namespaces organisiert werden, auf die die
meisten Agenten neben domänenspezifischen zugreifen.

**Agenten-Instanzen-Planung**: Überlegen Sie, welche Namespace-Kombinationen als Agenten-Instanzen bereitgestellt werden
sollen. Wenn Benutzergruppen Zugriff auf bestimmte Wissens-Teilmengen benötigen, organisieren Sie diese Teilmengen als
kohärente Namespace-Sammlungen, die dedizierten Agenten-Instanzen zugewiesen werden können.
