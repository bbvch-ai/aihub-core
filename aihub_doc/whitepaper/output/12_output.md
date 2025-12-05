# Kapitel 12: User Experience und Interaktion

## Die Brücke zwischen Technologie und Anwender

Die leistungsfähigste KI-Infrastruktur im Backend bleibt wirkungslos, wenn sie an der «letzten Meile» scheitert: der
Akzeptanz durch die Mitarbeitenden. In der Praxis werden KI-Projekte selten durch technische Mängel der Modelle
ausgebremst, sondern durch Benutzeroberflächen, die unintuitiv sind, hohe Schulungsaufwände erfordern oder sich wie ein
Fremdkörper in den Arbeitsalltag drängen. Ein System, das kognitive Hürden aufbaut, wird umgangen.

Der Swiss AI Hub begegnet dieser Herausforderung mit einem kompromisslosen Fokus auf User Experience (UX). Die Plattform
stellt nicht nur eine technische Schnittstelle bereit, sondern liefert eine vollständige, integrierte Arbeitsumgebung.
Das Ziel ist es, die Barriere zwischen menschlicher Absicht und maschineller Ausführung so weit zu senken, dass die
Interaktion mit KI-Agenten so natürlich wird wie der Umgang mit E-Mail oder Textverarbeitung.

## Einheitliche Suite statt Applikations-Fragmentierung

### Reduktion der kognitiven Last

Mitarbeitende sind heute oft mit einer Vielzahl isolierter Tools konfrontiert, was zu ständigen Kontextwechseln und
einer steilen Lernkurve führt. Eine Enterprise-KI-Plattform sollte nicht als «noch ein weiteres Tool» wahrgenommen
werden, sondern als zentraler Hub, der verschiedene Assistenzfunktionen bündelt. Konsistenz in Design und Bedienung ist
dabei der Schlüssel zur Produktivität: Wer eine Funktion beherrscht, beherrscht intuitiv das gesamte System.

### Das integrierte Service-Portal

Der Swiss AI Hub realisiert diesen Anspruch durch eine Suite-Architektur, die stark an moderne Produktivitätsumgebungen
wie Microsoft Office oder Google Workspace angelehnt ist. Anstatt lose gekoppelter Einzelanwendungen authentifiziert
sich der Benutzer einmalig und erhält Zugriff auf ein kohärentes Ökosystem. Eine persistente Navigation und eine
durchgängige Designsprache verbinden die verschiedenen Module – von der Interaktion mit Agenten über die Verwaltung von
Wissensdatenbanken bis hin zur Analyse von Geschäftsprozessen.

Technisch bildet die Plattform eine stark erweiterte Version der **Open WebUI** als primäre Schnittstelle. Diese
Entscheidung ermöglicht es Unternehmen, von einer weltweit aktiven Open-Source-Community zu profitieren, während der
Swiss AI Hub unternehmensspezifische Erweiterungen für Sicherheit, Governance und RAG-Integration hinzufügt. Die
Oberfläche ist responsive gestaltet und kann als Progressive Web App (PWA) installiert werden. Dies garantiert, dass
Mitarbeitende auf Tablets oder Smartphones denselben Funktionsumfang nutzen können wie am Desktop, inklusive
Offline-Fähigkeiten und Push-Benachrichtigungen, ohne auf native App-Stores angewiesen zu sein.

## Multimodale Interaktion: Sprache, Bild und Dokumente

### Natürliche Eingabeformen für effiziente Arbeit

Die traditionelle Eingabe per Tastatur ist nicht immer der effizienteste Weg, um komplexe Sachverhalte zu kommunizieren.
In vielen Situationen – sei es unterwegs, bei der Analyse visueller Daten oder im kreativen Fluss – bremsen reine
Textinterfaces den Workflow. Eine moderne KI-Plattform muss daher multimodal agieren, also verschiedene Eingabeformen
parallel verstehen und verarbeiten.

### Flexible Eingabemethoden

Der Swiss AI Hub unterstützt eine breite Palette an Interaktionsmodi, die sich den Bedürfnissen des Nutzers anpassen:

- **Spracheingabe:** Über die integrierte Spracherkennung können Anweisungen diktiert statt getippt werden. Eine
  visuelle Zeitleiste zeigt die Dauer der Aufnahme an, bevor diese transkribiert wird. Die Modelle sind für Deutsch,
  Englisch, Französisch, Italienisch und spezifisch auch für Schweizerdeutsch optimiert. KI-Antworten können ebenfalls
  per Text-to-Speech vorgelesen werden, was Barrierefreiheit und «Eyes-free»-Szenarien ermöglicht.
- **Bildschirmfreigabe und Vision:** Nutzer können direkt aus dem Chat heraus Browser-Tabs, Fenster oder den gesamten
  Bildschirm freigeben. Die Plattform erfasst den Bildschirminhalt und ermöglicht es dem Nutzer, Fragen dazu zu stellen
  («Was zeigt dieser Graph?», «Fasse diese Tabelle zusammen»). Vision-fähige Modelle analysieren den visuellen Kontext
  und antworten direkt.
- **Dokumenten-Analyse:** Dateien (PDF, Office, Text) lassen sich per Drag-and-Drop in den Chat ziehen. Die KI
  verarbeitet diese Dokumente ad-hoc, um Fragen zu Inhalten zu beantworten oder Zusammenfassungen zu erstellen, ohne
  dass diese Dateien dauerhaft in einer Wissensdatenbank indiziert werden müssen.

## Kontext-Management und Nutzerkontrolle

### Kontinuität über Sitzungen hinweg

Geschäftsprozesse sind selten nach einer einzigen Frage abgeschlossen. Sie entwickeln sich über Tage oder Wochen. Ein
häufiges Defizit einfacher Chatbots ist die «Amnesie» – das Verlieren des Kontexts, sobald ein Fenster geschlossen wird.
Der Swiss AI Hub implementiert ein robustes Thread-Management, das alle Konversationen persistent speichert. Benutzer
können vergangene Diskussionen jederzeit wiederaufnehmen, Themenbereiche taggen (z.B. «Projekt X», «Recherche») oder
Unterhaltungen archivieren.

### Granulare Historienverwaltung

Die Plattform gewährt dem Nutzer die volle Souveränität über seine Historie. Nachrichten können nachträglich bearbeitet
werden, um Missverständnisse zu korrigieren, woraufhin die KI ihre Antwort basierend auf dem neuen Kontext regeneriert
(«Time Travel»). Diese Flexibilität verhindert, dass bei einem Tippfehler der gesamte Dialog neu gestartet werden muss.

Aus Datenschutzperspektive ist die Kontrolle über diese Daten entscheidend. Die Plattform bietet Funktionen zum
Exportieren von Chat-Verläufen sowie zum unwiderruflichen Löschen einzelner Threads oder des gesamten Benutzerprofils.
Dies stellt sicher, dass die Anforderungen des revDSG und der DSGVO direkt durch den Endanwender umgesetzt werden
können.

## Transparenz und Quellen-Attribution

### Vertrauen durch Verifizierbarkeit

In einem geschäftlichen Kontext ist eine KI-Antwort nur so wertvoll wie ihre Glaubwürdigkeit. Mitarbeitende müssen in
der Lage sein, die Aussagen der KI gegen interne Originaldokumente zu prüfen, um fundierte Entscheidungen zu treffen.
Eine «Black Box», die Ergebnisse ohne Begründung liefert, wird in qualitätskritischen Prozessen nicht akzeptiert.

### Interaktive Zitation

Der Swiss AI Hub integriert Mechanismen zur Quellen-Transparenz direkt in die Benutzeroberfläche. Sobald ein Agent auf
eine **Wissensdatenbank** zugreift (Retrieval-Augmented Generation), wird die Antwort mit interaktiven Fussnoten
versehen. Ein Klick auf eine Referenz öffnet ein seitliches Panel, das nicht nur den Namen des Quelldokuments anzeigt,
sondern die exakte Textpassage hervorhebt, die zur Generierung der Antwort verwendet wurde. Dies ermöglicht einen
sofortigen Faktencheck, ohne den Lesefluss zu unterbrechen.

### Feedback-System und Evaluation

Um die Qualität der Agenten kontinuierlich zu verbessern, können Nutzer Antworten direkt bewerten (Daumen hoch/runter).
Im erweiterten Modus können detaillierte Rückmeldungen zur Qualität (z.B. «zu lang», «faktisch falsch») gegeben werden.

Zusätzlich unterstützt die Plattform einen «Arena-Modus» für den objektiven Modellvergleich. Hierbei werden Antworten
verschiedener Modelle (z.B. GPT-4o vs. Mistral Large) anonymisiert gegenübergestellt. Die Nutzerwahl fliesst in ein
internes Elo-Rating-System ein. Diese datengestützte Evaluation hilft Administratoren, die effektivsten Modelle für
spezifische Anwendungsfälle zu identifizieren, basierend auf der tatsächlichen Zufriedenheit der Mitarbeitenden und
nicht nur auf synthetischen Benchmarks.

## Omni-Channel-Integration: Teams und Slack

### KI dort, wo die Zusammenarbeit stattfindet

Während die Web-Oberfläche für komplexe Analysen ideal ist, finden schnelle Abstimmungen oft in Kollaborationstools
statt. Um Medienbrüche zu vermeiden, integriert der Swiss AI Hub Agenten nativ in **Microsoft Teams** und **Slack**.

Über die Integration des Azure Bot Service agieren Agenten als natürliche Teammitglieder. Ein Nutzer kann einen Agenten
in einem Teams-Kanal erwähnen («@Helpdesk, wie ist der Status von Ticket 123?»), und der Agent antwortet direkt im
Thread. Dank Streaming-Unterstützung wird die Antwort in Echtzeit aufgebaut, was die gefühlte Latenz minimiert. Diese
Integration unterstützt auch «Human-in-the-Loop»-Szenarien: Agenten können bei Unsicherheiten proaktiv Experten in einem
Slack-Kanal um Rat fragen, deren Antwort verarbeiten und den Workflow autonom fortsetzen.

## Internationalisierung und Schweizer Lokalisierung

### Mehrsprachigkeit als Standard

Für Schweizer Organisationen ist die Unterstützung der Landessprachen keine Zusatzfunktion, sondern eine
Grundvoraussetzung. Eine Benutzeroberfläche, die nur auf Englisch verfügbar ist, führt zu Akzeptanzproblemen und kann
regulatorische Vorgaben verletzen.

Die Architektur des Swiss AI Hub ist von Grund auf internationalisiert. Die gesamte Benutzeroberfläche – von Menüs über
Hilfetexte bis hin zu Fehlermeldungen – ist vollständig in Deutsch, Französisch, Italienisch und Englisch lokalisiert.
Die Sprachwahl erfolgt pro Benutzerprofil, kann aber bei Bedarf temporär für eine Sitzung gewechselt werden.

Wichtiger als die Übersetzung der Oberfläche ist die linguistische Kompetenz bei der Verarbeitung: Die Plattform
berücksichtigt bei der Suche und Indexierung von Dokumenten die Besonderheiten der jeweiligen Sprache (z.B. Stemming).
Auch Datums-, Zeit- und Zahlenformate passen sich automatisch den regionalen Konventionen an (z.B. 31.12.2024 vs.
12/31/2024). Dies garantiert, dass sich die Plattform für einen Nutzer in der Romandie genauso nativ anfühlt wie für
einen Kollegen in der Deutschschweiz oder im Tessin.
