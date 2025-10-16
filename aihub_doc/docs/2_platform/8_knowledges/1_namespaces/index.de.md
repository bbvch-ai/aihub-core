---
title: Wissensorganisation durch Namespaces
index: 1
source_sha: "6b0c9a62393e836dea11d31aebbca12ae89da515e0c30241b06f7c20841aeb0b"
---

# Wissensorganisation durch Namespaces

Der Swiss AI-Hub organisiert Unternehmenswissen mithilfe einer Namespace-basierten Architektur, die eine logische Trennung,
flexible Zugriffskontrolle und ein unabhängiges Lifecycle-Management für verschiedene Wissensbereiche bietet. Dieser Ansatz ermöglicht es
Organisationen, ihre Wissensbasen so zu strukturieren, dass sie die Geschäftsrealität widerspiegeln, während gleichzeitig die Abrufleistung
und das operative Management optimiert werden.

## Das Namespace-Konzept

Namespaces fungieren als logische Container für verwandte Dokumente und Informationen, ähnlich wie Ordner in einem Dateisystem, aber
optimiert für die Vektorähnlichkeitssuche. Jeder Namespace repräsentiert einen eigenen Wissensbereich – eine Produktlinie, Geschäftseinheit,
ein regulatorisches Framework oder jede andere logische Gruppierung, die für die Organisation von Bedeutung ist. Dokumente, die in den
Vektorspeicher aufgenommen werden, erhalten Namespace-Zuweisungen als Metadaten, was eine präzise Zielausrichtung bei Abrufoperationen ermöglicht.

Im Gegensatz zu traditionellen Ordnerhierarchien existieren Namespaces als flache Metadatenattribute, die jedem Dokument-Chunk im
Vektorspeicher zugeordnet sind. Diese flache Struktur ermöglicht es Agenten, gleichzeitig über mehrere Namespaces hinweg zu suchen,
ohne hierarchische Pfade navigieren zu müssen. Dies kombiniert die organisatorischen Vorteile der Kategorisierung mit den
Leistungsvorteilen der direkten Metadatenfilterung.

## Zugriffskontrolle auf Agenten-Ebene

Die Plattform implementiert eine Namespace-Zugriffskontrolle auf Agenten-Ebene: Wenn ein Agent für den Zugriff auf bestimmte Namespaces
konfiguriert ist, **erhält jeder Benutzer, der mit diesem Agenten interagiert, Antworten basierend auf demselben Wissensset**. Dies
gewährleistet ein konsistentes, vorhersehbares Agentenverhalten und vereinfacht Tests und Validierungen.

**Zugriffsphilosophie**: Agenten sind aufgabenorientierte Tools, die mit dem für ihre zugewiesene Funktion erforderlichen Wissen konfiguriert sind.
Die Zugriffskontrolle erfolgt auf Agenten-Ebene – wenn Benutzer keine Informationen innerhalb der Namespaces eines Agenten abrufen sollen,
sollten sie keine Autorisierung zur Nutzung dieses Agenten erhalten.

**Agenten-Wiederverwendbarkeit**: Derselbe Agenten-Workflow kann mehrfach mit unterschiedlichen Namespace-Konfigurationen instanziiert werden,
wodurch separate Instanzen für verschiedene Zielgruppen entstehen. Zum Beispiel könnte ein Support-Agenten-Workflow wie folgt bereitgestellt werden:

- **Öffentlicher Support-Agent**: Nur öffentliche Dokumentation, für alle Kunden verfügbar
- **Partner-Support-Agent**: Öffentliche und partnerspezifische Namespaces, für autorisierte Partner
- **Interner Support-Agent**: Vollständiger Zugriff, einschließlich interner technischer Dokumentation, nur für Mitarbeiter

Jede Instanz verwendet eine identische Workflow-Logik, operiert jedoch auf unterschiedlichen Wissensbereichen, wodurch ein angemessener
Informationszugriff ohne komplexe Pro-Benutzer-Filterung gewährleistet wird.

**Optionale Benutzervalidierung**: Organisationen können optional überprüfen, ob Benutzer Berechtigungen für alle Namespaces besitzen, auf die
ein Agent zugreift. Wenn aktiviert, prüft die Plattform die Benutzerberechtigungen vor der Workflow-Ausführung – Benutzer erhalten
entweder die vollen Agentenfunktionen oder eine klare Ablehnung, niemals Teilergebnisse.

## Wissenszugriffsmuster

**Domänenspezialisierung**: Spezialisierte Agenten konzentrieren sich auf bestimmte Wissensbereiche, indem sie den Namespace-Zugriff einschränken.
Ein Agent für regulatorische Compliance könnte nur auf rechtliche und Compliance-Namespaces zugreifen, während ein Produktsupport-Agent
auf technische Dokumentation zugreift. Diese Spezialisierung verbessert die Abruf-Relevanz, indem sie eine Kontamination durch irrelevante
Informationen verhindert.

**Multi-Domain-Agenten**: Agenten, die ein breiteres Wissen benötigen, spezifizieren mehrere Namespaces in ihrer Abrufkonfiguration.
Die Plattform führt den Abruf über alle konfigurierten Namespaces parallel durch und führt die Ergebnisse anhand von Relevanzwerten
zusammen, um die relevantesten Informationen unabhängig vom Namespace-Ursprung zu präsentieren.

**Dynamische Bereichsanpassung**: Organisationen ändern den Namespace-Zugriff von Agenten durch Konfigurationsaktualisierungen ohne Codeänderungen.
Das Hinzufügen einer neuen Produktlinie erfordert lediglich die Aktualisierung der Agentenkonfigurationen, um den neuen Namespace einzuschließen,
wodurch dieses Wissen sofort verfügbar gemacht wird.

## Operationelle Vorteile

**Unabhängige Updates**: Organisationen können Wissen in einem Namespace aktualisieren, ohne andere zu beeinflussen. Das Testen neuer
Ingestionspipelines kann in isolierten Namespaces erfolgen, ohne die Produktionsagenten zu beeinträchtigen, die auf etablierten Namespaces operieren.

**Zugriffskontrolle durch Bereitstellung**: Organisationen deployen mehrere Agenten-Instanzen mit unterschiedlichen Namespace-Konfigurationen
und steuern, welche Benutzer auf welche Agenten zugreifen. Mitarbeiter mit entsprechenden Freigaben greifen auf Agenten zu, die mit vertraulichen
Namespaces konfiguriert sind, während Auftragnehmer auf separate Instanzen zugreifen, die nur öffentlich teilbare Namespaces enthalten.

**Performance-Optimierung**: Die Einschränkung des Abrufs auf relevante Namespaces reduziert den Suchraum und verbessert sowohl
Geschwindigkeit als auch Relevanz. Wenn Wissensbasen wachsen, verhindert der Namespace-fokussierte Abruf eine Leistungsverschlechterung
– Agenten behalten eine konsistente Leistung bei, unabhängig von der Gesamtgröße der Wissensbasis.

**Lifecycle-Management**: Verschiedene Namespaces folgen unterschiedlichen Aufbewahrungsrichtlinien und Update-Zyklen. Rechtsdokumente
erfordern eine lange Aufbewahrung mit seltenen Updates, während Produktspezifikationen häufig aktualisiert werden, aber nach der Einstellung ablaufen.
Organisationen können inaktive Namespaces archivieren, ohne die aktuellen Agenten zu beeinflussen.

## Design-Überlegungen

Ein effektives Namespace-Design gleicht mehrere Faktoren aus:

**Granularität**: Namespaces definieren die feinste Granularität der Zugriffskontrolle. Die meisten Organisationen finden die optimale
Granularität auf Ebene der Geschäftseinheit, Produktfamilie oder des Funktionsbereichs – grob genug, um eine übermäßige Agentenproliferation
zu vermeiden, fein genug, um eine sinnvolle Zugriffs-Differenzierung zu ermöglichen.

**Stabilität**: Namespace-Strukturen sollten über die Zeit relativ stabil bleiben, da Reorganisationen eine erneute Ingestion
und Agenten-Rekonfiguration erfordern. Entwerfen Sie Schemata, die Geschäftswachstum ohne häufige Umstrukturierungen berücksichtigen.

**Auffindbarkeit**: Klare Namenskonventionen und Dokumentationen helfen Administratoren zu verstehen, welche Namespaces relevantes
Wissen für bestimmte Agentenrollen bereitstellen und welche Kombinationen geeignete Zugriffs-Scopes ermöglichen.

**Übergreifende Anliegen (Cross-Cutting Concerns)**: Informationen, die sich über mehrere Domänen erstrecken (Sicherheitsrichtlinien,
Markenrichtlinien), können über Namespaces hinweg dupliziert oder in dedizierten übergreifenden Namespaces organisiert werden,
auf die die meisten Agenten neben domänenspezifischen zugreifen.

**Agenteninstanz-Planung**: Berücksichtigen Sie, welche Namespace-Kombinationen als Agenteninstanzen bereitgestellt werden sollen.
Wenn Benutzergruppen Zugriff auf bestimmte Wissens-Teilmengen benötigen, organisieren Sie diese Teilmengen als kohärente Namespace-Sammlungen,
die dedizierten Agenteninstanzen zugewiesen werden können.
