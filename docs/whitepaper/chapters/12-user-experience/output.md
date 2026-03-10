# Kapitel 12: User Experience und Interaktion

Die Akzeptanz einer Enterprise-KI-Plattform steht und fällt mit ihrer Benutzerfreundlichkeit. Selbst die
leistungsfähigsten Modelle und sichersten Architekturen bleiben wirkungslos, wenn die Bedienung komplex ist oder
etablierte Arbeitsweisen stört. Mitarbeitende erwarten heute von Unternehmenssoftware denselben Komfort («Consumer Grade
Experience»), den sie von privaten Applikationen gewohnt sind – ohne dabei Kompromisse bei der Datensicherheit
einzugehen.

Dieses Kapitel beleuchtet die Interaktionsschicht des Swiss AI Hub. Es zeigt auf, wie die Plattform durch eine
integrierte Suite, multimodale Eingaben und eine radikale Transparenz Vertrauen schafft und Barrieren abbaut, um KI von
einem Expertenwerkzeug zu einem intuitiven Begleiter für die gesamte Belegschaft zu transformieren.

## Auf einen Blick

- **Integrierte Produktivitäts-Suite:** Eine einheitliche Benutzeroberfläche bündelt Chat, Wissensverwaltung,
  Prozessmonitoring und Evaluation, um Kontextwechsel zu minimieren.
- **Barrierefreie Multimodalität:** Die nahtlose Unterstützung von Spracheingabe (inkl. Schweizerdeutsch),
  Dokumenten-Uploads und Vision-Fähigkeiten ermöglicht natürliche Interaktionsformen.
- **Evidenzbasierte Transparenz:** KI-Antworten werden durch interaktive Zitationen direkt mit den Quellen verknüpft,
  während Tracing-Dashboards die Argumentationskette der Agenten offenlegen.
- **Kanal-Unabhängigkeit:** Durch die Integration in Microsoft Teams und Slack holt die Plattform den Nutzer dort ab, wo
  die Zusammenarbeit stattfindet, inklusive Experten-Eskalation («Bot-in-the-Loop»).
- **Nutzerzentrierte Datenhoheit:** Granulare Funktionen für den Export und die Löschung von Chat-Verläufen sowie die
  Verwaltung des Benutzergedächtnisses sichern die Einhaltung von Betroffenenrechten.

## Die integrierte Suite («Integrated Productivity Suite»)

### Geschäftlicher Nutzen

In vielen Unternehmen führt die Einführung von KI zu einer gefährlichen Tool-Fragmentierung. Mitarbeitende müssen
zwischen isolierten Anwendungen wechseln – einem Chatbot für HR-Fragen, einem separaten Tool für die Dokumentenanalyse
und einem weiteren für das Prozessmonitoring. Dieser ständige Kontextwechsel («Context Switching») vernichtet
Produktivität und erhöht den Schulungsaufwand massiv. Unternehmen benötigen eine zentrale Anlaufstelle, die alle
KI-Dienste unter einer einheitlichen Oberfläche bündelt. Dies reduziert die Lernkurve, da Navigationskonzepte und
Designsprache konsistent bleiben, und steigert die Effizienz durch einen nahtlosen Informationsfluss zwischen den
Diensten.

### Konzeptioneller Ansatz

Der Swiss AI Hub verfolgt den Ansatz einer integrierten Suite, vergleichbar mit modernen Office-Umgebungen. Die
Benutzeroberfläche ist kein loses Sammelsurium von Werkzeugen, sondern ein kohärentes Ökosystem. Ein zentraler
Service-Katalog dient als Einstiegspunkt für alle autorisierten Rollen. Das Design-Prinzip der Kontext-Persistenz stellt
sicher, dass Nutzer nahtlos zwischen Aufgaben wechseln können – etwa von der Analyse eines Dokuments im
Wissensmanagement direkt zur Interaktion mit einem darauf spezialisierten Agenten-Profil –, ohne den Faden zu verlieren.
Das System passt sich dabei durch dynamische Dienstsichtbarkeit («Security by Invisibility») automatisch an die
Berechtigungen des Nutzers an.

### Technische Umsetzung im Swiss AI Hub

Die Benutzeroberfläche basiert auf einer tief integrierten Implementierung der Open WebUI, die als primäre
Chat-Schnittstelle dient und um unternehmensspezifische Module erweitert wurde:

- **Zentraler Service-Katalog:** Über eine persistente Seitenleiste greifen Nutzer auf spezialisierte Dienste zu:
  Agentenverwaltung, Thread-Management (Konversationshistorie), Wissensverwaltung, Prozessverwaltung und den
  Evaluierungsdienst.
- **Intelligentes UI-Framework:** Die Oberfläche nutzt WebSockets für Echtzeit-Updates und Streaming-Antworten
  («Token-by-Token»). Skeleton-Screens sorgen für eine gefühlte hohe Performance während der Ladezeiten.
- **Integrationsarchitektur:** Open WebUI ist via iframe eingebettet und kommuniziert über eine sichere PostMessage-API
  mit der Suite-Plattform. Dies ermöglicht die Synchronisation von Authentifizierung (SSO) und den Austausch von
  Metadaten zwischen Chat und Backend-Diensten.
- **PWA-Unterstützung:** Die Plattform kann als Progressive Web App installiert werden, was eine native Nutzung auf
  mobilen Endgeräten inklusive Push-Benachrichtigungen ermöglicht.

## Multimodale Interaktion und Barrierefreiheit

### Geschäftlicher Nutzen

Menschliche Kommunikation ist nicht auf getippten Text beschränkt. In vielen Arbeitssituationen – etwa im Aussendienst,
bei der schnellen Erfassung von Sitzungsprotokollen oder bei der Analyse von Diagrammen – ist die Tastatur ein
Hindernis. Eine inklusive Plattform muss verschiedene Eingabekanäle unterstützen, um Barrieren abzubauen. Zudem ist in
der Schweiz die Unterstützung lokaler Landessprachen und Dialekte eine Grundvoraussetzung für die Akzeptanz. Eine
multimodale Schnittstelle erhöht die Datenerfassungsgeschwindigkeit und ermöglicht es auch Mitarbeitenden mit physischen
Einschränkungen, die Vorteile der KI uneingeschränkt zu nutzen.

### Konzeptioneller Ansatz

Die Plattform löst sich von der reinen Text-Eingabe und ermöglicht eine intuitive, multimodale Interaktion. Nutzer
können mit dem System sprechen, Bilder zur Analyse hochladen oder Dokumente per Drag-and-Drop direkt in einen Chat
ziehen. Das Konzept sieht vor, dass die KI den Kontext unabhängig vom Medium versteht. Ein gesprochener Satz wird ebenso
präzise verarbeitet wie ein hochgeladener Screenshot einer Fehlermeldung. Durch die Integration von Vision-Modellen
transformiert sich die KI von einem reinen Text-Statisten zu einem visuellen Partner, der komplexe Informationen
interpretieren kann.

### Technische Umsetzung im Swiss AI Hub

Der Swiss AI Hub integriert fortschrittliche Eingabetechnologien direkt in die Schnittstelle:

- **Sprachverarbeitung:** Über eine integrierte Aufnahmefunktion können Nachrichten diktiert werden. Die Plattform
  unterstützt Transkription für Deutsch (inkl. Schweizerdeutsch), Französisch, Italienisch und Englisch. Antworten
  können via Text-to-Speech vorgelesen werden.
- **Ad-hoc RAG & Dokumenten-Interaktion:** Dateien (PDF, Office, TXT) lassen sich direkt in den Chat hochladen. Die
  Plattform nutzt spezialisierte Parser wie PyMuPDF, um Inhalte sofort für den Agenten zugänglich zu machen, ohne sie
  permanent in eine Wissensdatenbank ingestieren zu müssen.
- **Vision-Fähigkeiten:** Nutzer können Bilder oder Screenshots einfügen. Modelle mit Sehfunktionen analysieren diese,
  extrahieren Texte oder erklären komplexe Diagramme und Mermaid-Visualisierungen.
- **Markdown- & LaTeX-Support:** Antworten werden reichhaltig formatiert dargestellt, einschliesslich mathematischer
  Notationen, Tabellen und Code-Blöcken mit Syntaxhervorhebung.

## Vertrauen durch Quellentransparenz und Datenkontrolle

### Geschäftlicher Nutzen

KI-Antworten sind im geschäftlichen Umfeld nur dann wertvoll, wenn sie verifizierbar sind. Nutzer müssen wissen, ob eine
Aussage auf einer aktuellen Richtlinie basiert oder eine Halluzination des Modells ist. Transparenz ist der Schlüssel
zur Risikominimierung und zur Einhaltung regulatorischer Vorgaben wie dem revDSG. Gleichzeitig müssen Nutzer die volle
Kontrolle über ihre digitalen Spuren behalten. Die Möglichkeit, eigene Daten einzusehen, zu exportieren oder zu löschen,
ist nicht nur ein Komfortmerkmal, sondern eine rechtliche Notwendigkeit zur Erfüllung von Betroffenenrechten.

### Konzeptioneller Ansatz

Um dem «Black-Box-Phänomen» entgegenzuwirken, implementiert die Plattform Mechanismen zur evidenzbasierten Interaktion.
Jede Behauptung eines Agenten, die auf Retrieval-Augmented Generation (RAG) beruht, wird proaktiv mit Belegen
untermauert. Parallel dazu wird die Argumentationskette des Agenten (Tracing) offengelegt. Das Konzept der Datenhoheit
wird durch ein dediziertes Gedächtnis-Management ergänzt, bei dem Nutzer genau steuern können, welche persönlichen
Präferenzen sich das System über Konversationen hinweg merken darf.

### Technische Umsetzung im Swiss AI Hub

- **Interaktives Quellen-Panel:** Bei RAG-Antworten werden Referenzen eingeblendet. Ein Klick öffnet ein Panel mit dem
  Originaltext-Abschnitt («Chunk»), den Metadaten des Dokuments und dem Relevanz-Score.
- **Observability-Integration:** Über eine Ereignisanzeige (basierend auf Arize Phoenix) können Nutzer die
  «Gedankenschritte» eines Agenten einsehen – von der Tool-Wahl bis zur Datenabfrage.
- **Gedächtnisverwaltung:** Der Benutzerspeicher erlaubt es, gelernte Fakten (z. B. «Nutzer bevorzugt Python»)
  einzusehen, zu korrigieren oder zu löschen. Das Organisationsgedächtnis dient hingegen als geteilte Faktenbasis für
  das gesamte Unternehmen.
- **Feedback-System & Arena-Modus:** Nutzer können Antworten bewerten. Im Arena-Modus können zwei Modelle parallel
  verglichen werden, wobei die Bewertungen in ein internes Elo-Rating einfliessen, um die besten Modelle für spezifische
  Aufgaben zu identifizieren.

## Nahtlose Integration in den Arbeitsalltag

### Geschäftlicher Nutzen

Die effektivste KI ist jene, die dort präsent ist, wo die Zusammenarbeit bereits stattfindet. Wenn Mitarbeitende ihren
gewohnten Arbeitsplatz in Microsoft Teams oder Slack verlassen müssen, um eine KI zu konsultieren, entsteht eine Hürde,
die die Nutzungshäufigkeit senkt. Durch die Einbettung der KI in bestehende Kanäle wird sie zu einem virtuellen
Teammitglied. Dies ermöglicht nicht nur schnellere Antworten, sondern auch hybride Workflows, bei denen die KI bei
komplexen Entscheidungen menschliche Experten proaktiv einbezieht.

### Konzeptioneller Ansatz

Der Swiss AI Hub verfolgt eine Strategie der Kanal-Unabhängigkeit. Die Plattform fungiert als zentrales Hirn, das
verschiedene Kommunikationskanäle gleichzeitig bedient. Das Konzept des «Bot-in-the-Loop» ermöglicht es KI-Agenten,
Aufgaben autonom zu bearbeiten und bei Bedarf Experten-Feedback via Messenger einzuholen. Sobald der Mensch antwortet,
nimmt der Agent den Kontext wieder auf und führt den Prozess fort. Dies sichert die Qualität und behält die menschliche
Kontrolle («Human Oversight») bei geschäftskritischen Aufgaben.

### Technische Umsetzung im Swiss AI Hub

Die Anbindung erfolgt über die Bot Framework API und den Azure Bot Service:

- **Native Messenger-Integration:** Agenten agieren als vollwertige Kontakte in Microsoft Teams und Slack. Sie
  unterstützen Thread-Kontexte, Datei-Uploads und Echtzeit-Streaming.
- **Eskalations-Workflows:** Agenten können strukturierte Fragen in Experten-Kanäle posten. Die Antwort des Menschen
  wird automatisch erfasst und in den laufenden Prozess integriert.
- **Zentrale Konfiguration:** Über die `bot_paths` in der MongoDB werden interne Routing-Pfade definiert, die festlegen,
  welches Agenten-Profil auf welche Kanal-Anfrage reagiert.
- **Datenschutz:** Für alle Messenger-Interaktionen gelten dieselben Aufbewahrungsrichtlinien (z. B. 30 Tage für
  ephemere Daten) und Sicherheitsstandards wie für die Web-Oberfläche.
