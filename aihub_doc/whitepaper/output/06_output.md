# Kapitel 06: Datenmanagement, Integration und Ingestion

Die Qualität einer KI-Lösung korreliert direkt mit der Qualität der Daten, auf die sie zugreift. Selbst das
leistungsfähigste Sprachmodell liefert unzuverlässige Ergebnisse, wenn es mit veralteten, fragmentierten oder
unstrukturierten Informationen gespeist wird. Während die Administration die organisatorischen Rahmenbedingungen
schafft, fokussiert sich dieses Kapitel auf den technologischen Maschinenraum: Wie wird unstrukturiertes
Unternehmenswissen – von der PDF-Spezifikation bis zum SharePoint-Wiki – effizient, sicher und automatisiert in eine
semantisch durchsuchbare Wissensbasis transformiert?

Der Swiss AI Hub implementiert hierfür keine einfachen Upload-Skripte, sondern eine industriell gefertigte
Daten-zu-Wissen-Pipeline. Dieser Ansatz garantiert, dass Unternehmensdaten nicht als statischer Datenfriedhof enden,
sondern als dynamisches Organisationsgedächtnis zur Verfügung stehen, das mit jeder neuen Information mitwächst und
dabei strikte Zugriffsgrenzen respektiert.

## Auf einen Blick

- **Hierarchische Wissensarchitektur:** Die strikte Trennung von Daten in Wissensdatenbanken und Sammlungen verhindert
  Kontext-Vermischung und ermöglicht präzises Retrieval-Scoping.
- **Strukturelle Verlinkung:** Durch «Structural Linking» und die automatische Generierung von Zusammenfassungen
  (Summary Nodes) verstehen Agenten nicht nur Textfragmente, sondern den gesamten Dokumentkontext.
- **Änderungsgetriebene Automatisierung:** Dank «Observable Assets» synchronisiert sich die Plattform automatisch mit
  Enterprise-Quellen wie SharePoint, was die Aktualität ohne manuellen Aufwand sichert.
- **Institutionelles Gedächtnis:** Das Organisationsgedächtnis erlaubt es, Fakten und Richtlinien zentral zu
  hinterlegen, sodass alle Agenten auf einer konsistenten, geteilten Faktenbasis operieren.
- **Integrierte Ingestion-Sicherheit:** Jede Datei durchläuft strikte Validierungen (MIME-Type, Malware-Checks) und eine
  automatisierte Anonymisierung von PII, bevor sie verarbeitet wird.

## Strukturierte Wissensarchitektur und Scoping

### Geschäftlicher Nutzen

Ein zentrales Problem vieler KI-Pilotprojekte ist die «Kontext-Verwässerung». Wenn ein KI-Agent Zugriff auf ungefilterte
Datenmengen hat, vermischen sich Informationen aus der Lohnbuchhaltung mit IT-Handbüchern oder veralteten
Projektnotizen. Dies führt zu ungenauen Antworten und birgt das Risiko, dass sensible Informationen im falschen Kontext
auftauchen. Unternehmen benötigen eine Struktur, die Wissen logisch isoliert und sicherstellt, dass ein Agent nur jene
Datenpools konsultiert, die für seine spezifische Aufgabe autorisiert wurden. Nur so lässt sich die Genauigkeit erhöhen
und das «Need-to-know»-Prinzip auf Datenebene technisch durchsetzen.

### Konzeptioneller Ansatz

Die Plattform organisiert Wissen in einer dreistufigen Hierarchie: Wissensdatenbanken, Sammlungen (Namespaces) und
Dokumente. Wissensdatenbanken fungieren als oberste Isolationsbehälter für ganze Abteilungen oder Sensitivitätsstufen.
Innerhalb dieser Datenbanken erlauben Sammlungen eine thematische Gruppierung (z.B. «Richtlinien», «Handbücher»,
«Protokolle»).

Der entscheidende Vorteil liegt im «Collection-Scoping»: Ein Administrator weist einem Agenten-Profil nicht pauschal
eine Datenbank zu, sondern definiert exakt, welche Sammlungen für das Retrieval herangezogen werden. Die KI durchsucht
parallel nur diese autorisierten Bereiche, was die Suchgeschwindigkeit optimiert und Halluzinationen durch irrelevanten
Kontext unterbindet.

### Technische Umsetzung im Swiss AI Hub

Technisch realisiert der Swiss AI Hub diese Architektur durch eine entkoppelte Speicherschicht. Während die
Dokumentenmetadaten in FerretDB verwaltet werden, erfolgt die Vektorspeicherung in Milvus.

- **Wissensdatenbanken:** Jede Datenbank verfügt über eigene Konfigurationen und Berechtigungen.
- **Sammlungen (Namespaces):** Dokumente erhalten bei der Ingestion ein Sammlungs-Label. Da diese Strukturen flach und
  nicht verschachtelt sind, können Agenten hochperformant über mehrere Sammlungen hinweg suchen, ohne komplexe
  Verzeichnisbäume traversieren zu müssen.
- **Agenten-Integration:** In der Konfiguration des Agenten-Profils wird festgelegt, welche Sammlungen durchsucht
  werden. Das System führt diese Abfragen parallel aus und führt die Ergebnisse basierend auf Relevanz-Scores zusammen.

## Die Daten-zu-Wissen-Pipeline: Präzision durch Struktur

### Geschäftlicher Nutzen

Unstrukturierte Dokumente wie komplexe PDFs oder Excel-Tabellen sind für herkömmliche Algorithmen oft unlesbar.
Einfaches Text-Parsing zerstört den Zusammenhang; eine Tabellenzelle ohne ihre Kopfzeile verliert jede Bedeutung. Um
verlässliche Antworten zu generieren, muss die KI die logische Struktur eines Dokuments verstehen – Überschriften,
Listen und Tabellenhierarchien. Unternehmen benötigen eine Pipeline, die Dokumente nicht nur einliest, sondern deren
semantische Architektur rekonstruiert, um präzise Quellenangaben und kontextbezogene Antworten zu ermöglichen.

### Konzeptioneller Ansatz

Der Swiss AI Hub nutzt eine hochentwickelte Daten-zu-Wissen-Pipeline, die über das einfache Zerlegen von Text (Chunking)
hinausgeht. Der Prozess basiert auf «Deep Parsing» und «Structural Linking». Anstatt ein Dokument stur nach Zeichenlänge
zu schneiden, erkennt das System semantische Grenzen wie Kapitelwechsel.

Einzigartig ist die Erstellung eines Wissensgraphen: Jeder Textabschnitt (Chunk) wird sowohl sequentiell (mit seinem
Vorgänger/Nachfolger) als auch hierarchisch (mit einer Zusammenfassung des Kapitels) verknüpft. Findet der Agent eine
relevante Stelle, kann er über diese Links den Kontext erweitern («Context Window Expansion»), um die Antwortqualität
massiv zu steigern.

### Technische Umsetzung im Swiss AI Hub

Die Pipeline orchestriert mehrere spezialisierte Komponenten:

- **Docling:** Dieser Parser extrahiert Text, Tabellen und Strukturen aus PDFs und Office-Dateien unter Beibehaltung des
  Layouts.
- **Intelligentes Chunking:** Die Pipeline nutzt LlamaIndex, um Dokumente an logischen Grenzen zu teilen.
- **Summary Nodes:** Das System generiert via LLM automatisch hierarchische Zusammenfassungen für Dokumentabschnitte.
  Diese ermöglichen es dem Agenten, grosse Dokumentenmengen schnell zu überblicken.
- **Vektorisierung:** Text-Chunks werden mittels Embedding-Modellen transformiert und in Milvus gespeichert. Die
  Daten-Lineage wird dabei lückenlos gewahrt, sodass jede Antwort bis auf das exakte Textfragment im Quelldokument
  zurückverfolgt werden kann.

## Organisationsgedächtnis und geteilte Fakten

### Geschäftlicher Nutzen

In jeder Organisation existieren Fakten, die für alle KI-Agenten und Mitarbeitenden gleichermassen gelten – etwa
Deployment-Zyklen, Spesenreglemente oder IT-Standards. Es ist ineffizient, dieses Wissen redundant in jedem
Agenten-Profil zu hinterlegen. Zudem führt dies zu widersprüchlichen Aussagen, wenn Korrekturen nicht überall
nachgezogen werden. Ein zentrales Organisationsgedächtnis stellt sicher, dass Korrekturen an einem Fakt sofort allen
Agenten zugutekommen. Dies schafft Konsistenz und bewahrt institutionelles Wissen auch bei Mitarbeiterwechseln.

### Konzeptioneller Ansatz

Das Organisationsgedächtnis unterscheidet strikt zwischen individuellen Benutzerpräferenzen und objektiven
Unternehmensfakten. Während das Benutzergedächtnis personalisiert ist, basiert das Organisationsgedächtnis auf explizit
dokumentiertem Wissen. Es fungiert als geteilte Wissensbasis, auf die alle Agenten innerhalb eines Mandanten zugreifen
können. Durch die Zuweisung zu Namespaces (z.B. «Engineering», «HR») wird sichergestellt, dass Agenten nur relevante
Fakten abrufen, was die Präzision erhöht und Informationsüberflutung verhindert.

### Technische Umsetzung im Swiss AI Hub

Das Organisationsgedächtnis wird als spezialisierter Service innerhalb der Plattform verwaltet.

- **Explizite Dokumentation:** Fakten werden bewusst erstellt und mit Quellen (z.B. Richtliniendokumenten) verknüpft.
- **Semantische Suche & Graphtraversierung:** Agenten rufen Gedächtnisinhalte mittels Vektor-Ähnlichkeit ab und
  navigieren durch Beziehungen zwischen Konzepten (z.B. «Projekt X» verweist auf «Architektur Y»).
- **Audit-Trail:** Jede Änderung am Organisationsgedächtnis wird protokolliert (wer, wann, was), was die regulatorische
  Compliance unterstützt.

## Automatisierte Integration und Synchronisation

### Geschäftlicher Nutzen

Wissensmanagement scheitert oft an manuellem Aufwand. Sobald Dokumente manuell hochgeladen werden müssen, veralten sie
(«Stale Data»). Eine Enterprise-Lösung muss sicherstellen, dass die KI stets auf der «Source of Truth» arbeitet – sei es
ein SharePoint-Verzeichnis oder ein S3-Speicher. Automatisierte Konnektoren reduzieren den Pflegeaufwand und
garantieren, dass die KI neue Erkenntnisse oder gelöschte Dokumente nahezu in Echtzeit berücksichtigt, ohne dass die
IT-Abteilung intervenieren muss.

### Konzeptioneller Ansatz

Die Plattform verfolgt eine Strategie der änderungsgetriebenen Automatisierung. Anstatt Ressourcen durch nächtliche
Voll-Indizierungen zu verschwenden, überwachen Sensoren die Quellsysteme. Nur geänderte oder neue Dateien lösen die
Pipeline aus. Dabei gilt das Prinzip der Dokumenten-Isolation: Fehler bei der Verarbeitung einer einzelnen Datei stoppen
niemals die gesamte Pipeline. Datenbanken können entweder im manuellen Modus oder im «Auto-Sync»-Modus betrieben werden,
um Eindeutigkeit über die Datenquelle zu wahren.

### Technische Umsetzung im Swiss AI Hub

Die Orchestrierung erfolgt durch Dagster, eine Workflow-Engine für Data Engineering.

- **SharePoint-Konnektor:** Synchronisiert Dateien automatisch in den internen S3-Speicher (SeaweedFS).
- **Observable Assets:** Ein Job prüft regelmässig Hashes und Zeitstempel der Quellen. Bei Änderungen löst ein Sensor
  die Verarbeitung aus.
- **Lebenszyklus-Management:** Wird ein Dokument in der Quelle gelöscht, entfernt die Pipeline automatisch alle
  zugehörigen Vektoren, Chunks und Zusammenfassungen aus der Wissensdatenbank.

## Validierung und Sicherheit beim Import

### Geschäftlicher Nutzen

Der Import externer Dokumente ist ein potenzieller Angriffsvektor. Manipulierte Dateien könnten versuchen, die
Plattform-Infrastruktur zu kompromittieren oder die Vektordatenbank mit bösartigen Inhalten zu vergiften. Zudem müssen
Personenidentifizierbare Informationen (PII) geschützt werden, bevor sie verarbeitet oder an externe Sprachmodelle
gesendet werden. Eine robuste Ingestion-Pipeline muss daher als Sicherheitsfilter fungieren, der Dokumente validiert,
säubert und anonymisiert, bevor sie in das System integriert werden.

### Konzeptioneller Ansatz

Sicherheit ist integraler Bestandteil des Ingestion-Prozesses («Secure by Design»). Jede Datei wird als potenziell
unsicher betrachtet. Der Prozess umfasst die Prüfung auf Dateitypen (Whitelisting), Malware-Scans und den Schutz vor
Path-Traversal-Angriffen. Ein wesentlicher Bestandteil ist die automatische Erkennung und Maskierung von PII. Dies
stellt sicher, dass die Plattform auch in Umgebungen mit hohen Datenschutzanforderungen (revDSG) rechtssicher operiert.

### Technische Umsetzung im Swiss AI Hub

Die Plattform implementiert mehrstufige Sicherheitschecks:

- **MIME-Type & Whitelist:** Nur validierte Formate (ca. 40 Enterprise-Typen wie PDF, DOCX, JSON) werden akzeptiert. Die
  Erweiterung wird gegen den tatsächlichen Dateiinhalt geprüft.
- **Anonymisierung:** Integration von Presidio zur automatischen Maskierung sensibler Datenmuster während des
  Chunking-Prozesses.
- **Quarantäne & Audit:** Dokumente, die die Validierung nicht bestehen, werden isoliert und im Dagster-Audit-Log
  protokolliert.
- **Ressourcen-Limits:** Grössenbeschränkungen verhindern Denial-of-Service-Attacken durch manipulierte Grossdateien.
