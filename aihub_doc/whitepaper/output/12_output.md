# Kapitel 12: User Experience und Interaktion

Die Akzeptanz einer Enterprise-KI-Plattform steht und fällt mit ihrer Benutzerfreundlichkeit. Selbst die
leistungsfähigsten Modelle und sichersten Architekturen bleiben wirkungslos, wenn die Bedienung komplex ist oder
etablierte Arbeitsweisen stört. Mitarbeitende erwarten heute von Unternehmenssoftware denselben Komfort («Consumer Grade
Experience»), den sie von privaten Apps gewohnt sind – ohne dabei Kompromisse bei der Datensicherheit einzugehen.

Dieses Kapitel beleuchtet die Interaktionsschicht des Swiss AI Hub. Es zeigt auf, wie die Plattform durch eine
integrierte Suite, multimodale Eingaben und eine radikale Transparenz Vertrauen schafft und Barrieren abbaut, um KI von
einem Expertenwerkzeug zu einem intuitiven Begleiter für die gesamte Belegschaft zu transformieren.

## Auf einen Blick

- **Integrierte Produktivitäts-Suite:** Eine einheitliche Benutzeroberfläche bündelt Chat, Wissensverwaltung und
  Agenten-Steuerung, um Kontextwechsel zu minimieren und die Lernkurve flach zu halten.
- **Barrierefreie Multimodalität:** Nahtlose Unterstützung von Spracheingabe, Dokumenten-Uploads und direkter
  Bildschirmfreigabe ermöglicht natürliche Interaktionen jenseits von reinem Text.
- **Evidenzbasierte Transparenz:** KI-Antworten werden durch interaktive Zitationen direkt mit den Quellen aus der
  Wissensdatenbank verknüpft, was eine sofortige Faktenprüfung ermöglicht.
- **Kanal-Unabhängigkeit:** Durch native Integrationen in Microsoft Teams und Slack holt die Plattform den Nutzer dort
  ab, wo die Zusammenarbeit stattfindet, inklusive Experten-Eskalation («Bot-in-the-Loop»).
- **Schweizer Mehrsprachigkeit:** Die Oberfläche und Verarbeitung unterstützen nativ Deutsch, Französisch, Italienisch
  und Englisch, um den Anforderungen nationaler Organisationen gerecht zu werden.

## Eine integrierte Suite statt isolierter Tools

### Geschäftlicher Nutzen

In vielen Unternehmen führt die Einführung von KI zu einer Fragmentierung der Tool-Landschaft. Mitarbeitende müssen
zwischen verschiedenen Anwendungen wechseln – hier ein Chatbot für HR-Fragen, dort ein separates Tool für
Dokumentenanalyse. Dieser ständige Kontextwechsel («Context Switching») vernichtet Produktivität und erhöht den
Schulungsaufwand. Unternehmen benötigen eine zentrale Anlaufstelle, die verschiedene KI-Funktionalitäten unter einer
einheitlichen Oberfläche bündelt. Dies reduziert die Lernkurve drastisch, da Navigationskonzepte und Designsprache
konsistent bleiben, unabhängig davon, ob ein Agenten-Profil konfiguriert oder eine Wissensdatenbank durchsucht wird.

### Konzeptioneller Ansatz

Der Swiss AI Hub verfolgt den Ansatz einer integrierten Produktivitäts-Suite, vergleichbar mit modernen
Office-Umgebungen. Die Benutzeroberfläche ist nicht als Ansammlung loser Werkzeuge konzipiert, sondern als kohärentes
Ökosystem. Ein zentraler Service-Katalog dient als Einstiegspunkt. Das Design-Prinzip der Kontext-Persistenz stellt
sicher, dass Nutzer nahtlos zwischen Aufgaben – etwa der Analyse eines Dokuments und der anschliessenden Abfrage eines
Agenten – wechseln können, ohne den Faden zu verlieren. Die Authentifizierung erfolgt einmalig (Single Sign-On),
woraufhin alle autorisierten Dienste zur Verfügung stehen.

### Technische Umsetzung im Swiss AI Hub

Die Benutzeroberfläche basiert auf einer tief integrierten Implementierung der Open WebUI, die um
unternehmensspezifische Funktionen erweitert wurde:

- **Service-Katalog:** Nutzer finden hier alle verfügbaren Agenten, visualisiert mit Statusindikatoren und
  Beschreibungen. Ein Klick genügt, um eine Chat-Sitzung zu initiieren oder die zugrundeliegende Workflow-Logik
  einzusehen.
- **Persistente Navigation:** Eine permanente Seitenleiste ermöglicht den Zugriff auf Chat-Historie, Wissensverwaltung
  und Agenten-Steuerung von überall in der Applikation.
- **Intelligentes UI:** Die Oberfläche nutzt moderne Web-Technologien (WebSockets) für Echtzeit-Updates.
  Skeleton-Screens sorgen für eine gefühlte hohe Performance, während Agenten-Antworten als Stream («Token-by-Token»)
  dargestellt werden, sodass der Nutzer bereits lesen kann, während die Antwort noch generiert wird.
- **Artefakt-Verwaltung:** Nutzer können vergangene Chat-Verläufe durchsuchen, umbenennen, exportieren oder
  unwiderruflich löschen. Auch das Bearbeiten der eigenen letzten Nachricht ist möglich, um die Antwort des Agenten neu
  zu generieren.

## Multimodale Interaktion und Barrierefreiheit

### Geschäftlicher Nutzen

Menschliche Kommunikation ist nicht auf getippten Text beschränkt. In vielen Arbeitssituationen – etwa im Aussendienst,
im Spital oder bei der schnellen Erfassung von Ideen – ist die Tastatur ein Hindernis. Eine inklusive Plattform muss
verschiedene Eingabekanäle unterstützen, um Barrieren abzubauen und die Effizienz zu steigern. Zudem ist in der
mehrsprachigen Schweiz die Unterstützung der lokalen Landessprachen kein Luxus, sondern eine Grundvoraussetzung für die
breite Akzeptanz in der Verwaltung und in national tätigen Unternehmen.

### Konzeptioneller Ansatz

Die Plattform löst sich von der reinen Text-Eingabe und ermöglicht eine multimodale Interaktion. Nutzer können mit dem
System sprechen, Bilder zeigen oder Dokumente hochladen. Das Konzept sieht vor, dass die KI den Kontext unabhängig vom
Eingabemedium versteht. Ein gesprochener Satz wird ebenso präzise verarbeitet wie ein hochgeladener Screenshot einer
Fehlermeldung. Dies fördert nicht nur die Effizienz, sondern auch die Barrierefreiheit für Menschen mit Einschränkungen.

### Technische Umsetzung im Swiss AI Hub

Der Swiss AI Hub integriert fortschrittliche Eingabetechnologien direkt in die Chat-Oberfläche:

- **Spracheingabe:** Über das Mikrofon-Symbol können Nachrichten diktiert werden. Die Plattform unterstützt
  Transkription in Deutsch (inklusive Schweizerdeutsch), Englisch, Französisch und Italienisch. Antworten können auf
  Wunsch via Text-to-Speech vorgelesen werden, was insbesondere sehbehinderten Nutzern zugutekommt.
- **Bildschirmfreigabe und Vision:** Nutzer können über die Funktion «Aufnehmen» direkt Browser-Tabs, Fenster oder den
  gesamten Bildschirm teilen. Modelle mit Vision-Fähigkeiten analysieren diese visuellen Informationen – beispielsweise
  um Diagramme zu erklären oder Text aus einem Screenshot zu extrahieren.
- **Dokumenten-Interaktion:** Dateien (PDF, Office, Text) lassen sich per Drag-and-Drop in den Chat ziehen. Dies erlaubt
  «Ad-hoc RAG», bei dem Nutzer Fragen zu einem spezifischen Dokument stellen können, ohne es permanent in eine
  Wissensdatenbank ingestieren zu müssen.

## Vertrauen durch Quellentransparenz und Kontrolle

### Geschäftlicher Nutzen

In einem geschäftlichen Kontext ist eine KI-Antwort wertlos, wenn ihre Herkunft unklar ist. Nutzer müssen verifizieren
können, ob eine Aussage auf aktuellen Unternehmensrichtlinien basiert oder eine Halluzination des Modells ist. Mangelnde
Transparenz führt zu Misstrauen und verhindert den Einsatz in kritischen Prozessen. Zudem ist es für die kontinuierliche
Verbesserung der Systeme essenziell, dass Nutzer Feedback zur Qualität der Antworten geben können.

### Konzeptioneller Ansatz

Um dem «Black-Box»-Phänomen entgegenzuwirken, implementiert die Plattform Mechanismen zur evidenzbasierten Interaktion.
Jede Behauptung eines Agenten, die auf Retrieval-Augmented Generation (RAG) beruht, muss belegbar sein. Das Interface
stellt diese Belege proaktiv zur Verfügung, ohne den Lesefluss zu stören. Gleichzeitig werden Nutzer in den
Qualitätssicherungsprozess eingebunden, indem sie Antworten bewerten können, was wiederum die Optimierung der
Agenten-Profile steuert.

### Technische Umsetzung im Swiss AI Hub

Die Transparenz wird durch spezifische UI-Komponenten sichergestellt:

- **Interaktive Zitation:** Wenn ein Agent Wissen aus einer Wissensdatenbank nutzt, werden die verwendeten Referenzen
  direkt unter der Antwort angezeigt. Ein Klick auf die Zitation öffnet ein Seiten-Panel, das das Originaldokument, den
  exakten Textausschnitt («Chunk») und die Relevanz-Scores anzeigt. Dies ermöglicht eine sofortige Faktenprüfung.
- **Feedback-Schleife & Elo-Rating:** Nutzer können Antworten mit «Daumen hoch/runter» bewerten und schriftliches
  Feedback geben. Diese Daten fliessen in eine interne Bestenliste (Elo-Rating) ein, die Administratoren hilft, die
  effektivsten Modelle für spezifische Aufgaben zu identifizieren.
- **Gedanken-Protokoll:** Für komplexe Agenten-Workflows kann der Nutzer die «Gedankenschritte» (Thought Events)
  aufklappen. Dies visualisiert, welche Tools der Agent aufgerufen hat und wie er Schritt für Schritt zu seiner
  Schlussfolgerung gelangt ist.

## Nahtlose Integration in Kollaborations-Tools

### Geschäftlicher Nutzen

Die Einführung neuer Software scheitert oft an der Gewohnheit der Nutzer. Wenn Mitarbeitende ihren gewohnten
Arbeitsplatz – sei es Microsoft Teams oder Slack – verlassen müssen, um eine KI zu konsultieren, entsteht eine Hürde.
Die effektivste KI ist jene, die als «virtueller Kollege» dort präsent ist, wo die Zusammenarbeit im Team bereits
stattfindet. Dies senkt die Hemmschwelle zur Nutzung und ermöglicht es, KI-Support direkt in Gruppendiskussionen
einzubinden.

### Konzeptioneller Ansatz

Der Swiss AI Hub verfolgt eine Strategie der Kanal-Unabhängigkeit. Die Benutzeroberfläche ist nicht auf den Webbrowser
beschränkt. Durch die Integration in Messenger-Dienste wird die KI Teil des Teams. Das Konzept unterstützt dabei auch
hybride Arbeitsweisen: Ein Agent kann eine Aufgabe in Teams entgegennehmen, bei Unsicherheit einen menschlichen Experten
in einem definierten Kanal um Rat fragen («Bot-in-the-Loop») und nach Erhalt der Antwort den Prozess autonom fortsetzen.

### Technische Umsetzung im Swiss AI Hub

Die Anbindung erfolgt über den integrierten Azure Bot Service, der als Brücke zwischen der Plattform und den Kanälen
fungiert:

- **Native Clients:** In Microsoft Teams und Slack agiert der Agent als normaler Kontakt. Er unterstützt
  Rich-Text-Formatierung, Datei-Uploads und Streaming-Antworten (Tipp-Indikator), sodass sich die Interaktion natürlich
  anfühlt.
- **Kontext-Erhalt:** Die Plattform speichert den Konversationszustand persistent. Ein Nutzer kann eine Diskussion
  beginnen und später fortsetzen, da der Agent Zugriff auf die Historie hat.
- **Experten-Eskalation:** Über strukturierte Workflows können Agenten Fragen in Experten-Channels posten. Die Antwort
  des menschlichen Experten wird vom System erfasst und in den Wissenskontext des Agenten integriert, wodurch ein
  organisatorischer Lerneffekt entsteht.

## Lokalisierung und Internationalisierung

### Geschäftlicher Nutzen

Für Schweizer Organisationen ist die Unterstützung der Landessprachen essenziell. Eine Plattform, die nur auf Englisch
verfügbar ist oder schlechte Übersetzungen liefert, wird von der Belegschaft nicht akzeptiert. Behörden und Unternehmen
müssen sicherstellen, dass Mitarbeiter in der Deutschschweiz, der Romandie und im Tessin gleichberechtigten Zugang zu
den KI-Diensten haben.

### Konzeptioneller Ansatz

Internationalisierung ist tief im System verankert. Die Plattform unterscheidet zwischen der Sprache der
Benutzeroberfläche (statische Elemente) und der Sprache der generierten Inhalte. Nutzer können ihre bevorzugte Sprache
im Profil wählen, was sofortige Auswirkungen auf die gesamte Interaktion hat. Das System ist darauf ausgelegt, dynamisch
generierte Inhalte – wie Beschreibungen von Agenten oder Fehlermeldungen – ebenfalls in der Zielsprache auszugeben.

### Technische Umsetzung im Swiss AI Hub

- **Vollständige UI-Übersetzung:** Alle Menüs, Dialoge und Hilfetexte sind in Deutsch, Englisch, Französisch und
  Italienisch verfügbar. Fehlt eine Übersetzung, greift das System auf Deutsch zurück.
- **Formatierung:** Zahlen, Datumsangaben und Währungen werden automatisch gemäss den regionalen Konventionen der
  gewählten Sprache formatiert (z.B. «31.12.2024» für Deutsch vs. «12/31/2024» für Englisch).
- **Inhaltliche Adaption:** Dynamische Inhalte wie Namespace-Namen oder Agenten-Beschreibungen passen sich der gewählten
  Sprache an. Dies stellt sicher, dass Nutzer keine Sprachmischung erleben und sich intuitiv zurechtfinden.
