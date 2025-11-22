# Kapitel 12: User Experience und Interaktion

Die effektive Integration von Künstlicher Intelligenz (KI) in Schweizer Unternehmen hängt entscheidend von einer
intuitiven, zugänglichen und nahtlosen Benutzererfahrung ab. Angesichts der vielfältigen Anforderungen an
Barrierefreiheit, Mehrsprachigkeit und Datensouveränität benötigen Organisationen eine Plattform, die nicht nur
technologisch fortschrittlich ist, sondern sich auch nahtlos in den Arbeitsalltag der Nutzer einfügt. Dieses Kapitel
beleuchtet, wie der Swiss AI Hub eine herausragende Benutzererfahrung und Interaktion gewährleistet, indem er eine
konsistente Oberfläche über diverse Kanäle hinweg bietet, multimodale Eingabemöglichkeiten unterstützt und höchste
Ansprüche an Transparenz und Nutzerkontrolle erfüllt.

## 1. Ganzheitliche und intuitive Benutzeroberfläche

Die Akzeptanz von KI-Lösungen im Unternehmen steht und fällt mit der Benutzerfreundlichkeit. Eine fragmentierte
Tool-Landschaft mit inkonsistenten Designs und Bedienkonzepten erzeugt Reibungsverluste und hemmt die breite Einführung.

### Mehrwert und Nutzen: Maximale Nutzerakzeptanz und minimale Schulungsaufwände

Für C-Level-Führungskräfte bedeutet eine intuitiv bedienbare und konsistente Plattform eine schnelle Adaption durch die
Mitarbeitenden, was den Return on Investment (ROI) der KI-Investitionen beschleunigt. Eine geringe Lernkurve reduziert
Schulungsaufwände und beschleunigt die Time-to-Value. IT-Teams profitieren von einer standardisierten
Benutzeroberfläche, die den Support vereinfacht, die Fehlerquote minimiert und die flexible Anpassung an das Corporate
Design ermöglicht, ohne die Kernfunktionalität zu beeinträchtigen. Der "Design-for-All"-Ansatz gewährleistet eine
geräteunabhängige Zugänglichkeit, sodass Mitarbeitende jederzeit und überall produktiv sein können.

### Konzepte & Prozesse: Integrierte Suite und dynamischer Service-Katalog

Der Swiss AI Hub ist als integrierte Suite konzipiert, ähnlich etablierter Produktivitätssoftware. Anstatt isolierte
Anwendungen zu bündeln, bietet die Plattform ein einheitliches Navigationsframework und eine konsistente Designsprache
über alle Funktionen hinweg. Benutzer authentifizieren sich einmal, um auf eine kohärente Suite von KI-Diensten
zuzugreifen. Eine permanente Seitenleiste ermöglicht den direkten Zugriff auf jeden autorisierten Dienst, wodurch
Workflow-Unterbrechungen eliminiert werden. Die Benutzeroberfläche präsentiert dynamisch einen Service-Katalog, der
Benutzern auf Basis ihrer Rollen und Berechtigungen eine Reihe spezialisierter Dienste anzeigt – von der Agenten- und
Thread-Verwaltung über Wissensmanagement und Prozessautomatisierung bis hin zu Evaluationsdiensten. Die nahtlose
Navigation zwischen diesen Diensten ermöglicht einen ununterbrochenen Workflow, wobei der Kontext dienstübergreifend
fliessen kann.

### Technische Umsetzung im Swiss AI Hub: Open WebUI und anpassbares Design

Die primäre Chat-Schnittstelle des Swiss AI Hub basiert auf **Open WebUI**, einem etablierten Open-Source-Projekt, das
um unternehmensspezifische Funktionen erweitert und direkt in die Swiss AI Hub Suite eingebettet wurde. Ein konsistentes
visuelles Design und dieselben Interaktionsmuster sind über alle Dienste hinweg etabliert. Die **responsiven
Web-Komponenten** und die Möglichkeit der **Installation als Progressive Web App (PWA)** gewährleisten eine optimale
Darstellung und Funktionalität auf Desktops, Tablets und Mobiltelefonen. Ein umfassendes **White-Labeling** der
Chat-Interfaces und Web-Komponenten ermöglicht die Anpassung an das Unternehmensdesign (Logos, Farbschemata,
Schriftarten), um eine konsistente Markenführung zu sichern. Die Oberfläche nutzt zudem moderne Webmuster wie
Skeleton-Screens und Echtzeit-Updates über WebSockets, um ein schnelles und reaktionsschnelles Benutzererlebnis zu
gewährleisten. Die Barrierefreiheit (WCAG-Konformität) kann durch entsprechende Konfigurationen und Anpassungen
gewährleistet oder erreicht werden, wobei der "Design-for-All"-Ansatz als Kernprinzip der Plattform dient.

## 2. Multimodale Interaktion und natürliche Eingabemöglichkeiten

Moderne Arbeitsabläufe sind vielfältig und erfordern flexible Eingabemöglichkeiten. Die Beschränkung auf reine
Texteingaben kann die Effizienz mindern und die Barrierefreiheit einschränken.

### Mehrwert und Nutzen: Effizienz und inklusive Nutzung für alle Anwender

Für Führungskräfte ermöglicht die Unterstützung verschiedener Eingabemodalitäten eine signifikante Steigerung der
Arbeitseffizienz, da Mitarbeitende die für den jeweiligen Kontext natürlichste und schnellste Kommunikationsform wählen
können. Dies fördert eine breitere, inklusivere Nutzung der KI-Plattform, da auch sehbehinderte oder motorisch
eingeschränkte Personen problemlos interagieren können. IT-Teams profitieren von einer robusten Plattform, die den
Umgang mit heterogenen Datenformaten abstrahiert und eine hohe Qualität der Eingabedaten für KI-Modelle gewährleistet.

### Konzepte & Prozesse: Natürliche Interaktion und umfassende Datenerfassung

Der Swiss AI Hub unterstützt eine breite Palette an Interaktionsformen, um sich nahtlos in die Arbeitsabläufe der
Benutzer einzufügen. Benutzer können Textnachrichten eingeben, Sprachbefehle diktieren oder Dokumente und Bilder direkt
in Konversationen hochladen. Die Plattform verarbeitet diese unterschiedlichen Modalitäten parallel und kontextsensitiv,
um präzise und umfassende KI-Antworten zu generieren. Die multimodale Interaktion umfasst zudem die Fähigkeit,
KI-Antworten als Sprache auszugeben, was die Barrierefreiheit weiter verbessert.

### Technische Umsetzung im Swiss AI Hub: Sprache, Dokumente und Bildschirmfreigabe

Die Plattform bietet umfassende Kern-Chat-Funktionen wie Echtzeit-Nachrichten-Streaming, Konversationskontext über
mehrere Runden hinweg sowie die Möglichkeit, frühere Nachrichten zu bearbeiten, zu löschen oder Antworten neu zu
generieren. Für die **Spracheingabe** können Benutzer Nachrichten diktieren. Unterstützte Sprachen sind Englisch,
Deutsch und **Schweizerdeutsch**, wobei KI-Antworten auch als Sprache ausgegeben werden können. Benutzer können zudem
**Dokumente direkt in Konversationen hochladen** (PDFs, Office-Dokumente und Textdateien), typischerweise über einen
"Mehr"-Button und die Auswahl der Dateien. Diese Funktion ermöglicht es, Fragen zum Dokumenteninhalt zu stellen oder
eine Analyse anzufordern. Für visuell gestützte KI-Modelle können Benutzer auch **Bilder über Bildschirmfreigabe** in
Konversationen einfügen, um Analyse, Beschreibung oder Verarbeitung anzufordern.
`UNKLARHEIT IN DER DOKU - BITTE PRÜFEN: Eine explizite Erwähnung von Drag-and-Drop oder PDF/A-Unterstützung findet sich in der Quelldokumentation nicht.`

## 3. Kontextsensitive Dialogführung und Transparenz der KI-Ergebnisse

Ohne Kontext verlieren KI-Interaktionen schnell ihren Wert, und ohne Nachvollziehbarkeit bleibt das Vertrauen in
KI-generierte Antworten gering. Der "Black-Box"-Effekt ist eine der größten Hürden für die Akzeptanz in Unternehmen.

### Mehrwert und Nutzen: Präzise Antworten und untermauertes Vertrauen

Führungskräfte erhalten die Gewissheit, dass KI-Systeme präzise und konsistente Antworten liefern, die auf einer
nachvollziehbaren Faktenbasis beruhen. Die Quellenangaben erhöhen das Vertrauen in die KI-Antworten erheblich und
reduzieren das Risiko von "Halluzinationen". Für IT-Teams und Fachexperten ermöglicht die kontextsensitive Dialogführung
eine effizientere Problembehandlung, da die KI frühere Interaktionen berücksichtigt. Die Transparenz über die Herkunft
von Informationen und die Arbeitsweise des Agenten unterstützt Debugging, Qualitätsprüfung und die Einhaltung von
Compliance-Vorgaben.

### Konzepte & Prozesse: Persistenter Kontext, Quellenzuordnung und Feedback-Loops

Der Swiss AI Hub gewährleistet, dass Konversationen über die Zeit hinweg ihren Kontext behalten, sodass Anschlussfragen
und vertiefende Diskussionen möglich sind. Ein entscheidendes Konzept ist die **Quellenzuordnung (Source Attribution)**,
die genau anzeigt, welche Dokumente und Textpassagen aus der Wissensbasis eine KI-Antwort beeinflusst haben. Dieses
interaktive Quellenanzeigefeld ermöglicht die Überprüfung von Aussagen. Ergänzt wird dies durch detaillierte
**Ausführungsverfolgungen (Observability)**, die Einblicke in die Entscheidungslogik der Agenten geben, sowie durch
**Benutzerfeedback-Mechanismen**, die eine kontinuierliche Verbesserung der Modellleistung ermöglichen. Das System
verfolgt, welche Quelldokumente Agenten verwendet haben, was die Zitation und Überprüfung von Antworten ermöglicht.

### Technische Umsetzung im Swiss AI Hub: Thread-Verwaltung, Live-Tracing und interaktive Quellen

Der Dienst **Thread-Verwaltung** bietet eine vollständige Historie aller Konversationen, die bei Bedarf fortgesetzt
werden können, wobei der volle Kontext erhalten bleibt. Die **Quellenattribution** zeigt ein benutzerdefiniertes
Quellenanzeigefeld an, wenn KI-Antworten auf organisationsinternes Wissen verweisen. Benutzer können die spezifischen
Dokumente und Passagen einsehen, die die Antwort beeinflusst haben, und direkt zu den vollständigen Quelldokumenten im
Wissensmanagementdienst navigieren. Dies minimiert Halluzinationen und macht diese transparent. Die Quellenanzeige
koordiniert Daten aus dem Thread-Management, der Ereignisverfolgung und dem Wissensmanagement, wobei Quelldaten bei
Bedarf geladen werden.

Die **Beobachtbarkeit (Observability)** ist über die Phoenix Trace-Integration realisiert und zeigt die schrittweise
Agentenausführung, Argumentationsketten, Tool-Aufrufe und Entscheidungspunkte direkt in der Chat-Benutzeroberfläche.
Dieses Live-Tracing bleibt über Konversationssitzungen hinaus bestehen und basiert auf OpenInference Semantic
Conventions für KI-spezifische Telemetriedaten. Benutzer können zudem **Feedback** (Daumen hoch/runter) zu KI-Antworten
geben, was in ein Elo-basiertes Ranglistensystem fliesst, das die Modellleistung bewertet. Die Versionskontrolle für
Dokumente im Wissensmanagement (gemäss Kapitel 06) stellt sicher, dass veraltete Informationen konsistent entfernt und
relevante Versionen referenziert werden.
`UNKLARHEIT IN DER DOKU - BITTE PRÜFEN: Eine explizite Warnung bei externen Links (GDPR) wird in der Quelldokumentation nicht beschrieben.`
`UNKLARHEIT IN DER DOKU - BITTE PRÜFEN: Die Anzeige des Konfidenzgrades oder der Unsicherheit der KI-Antwort wird in der Quelldokumentation nicht als UI-Funktion beschrieben.`

## 4. Nutzerzentrierte Datenkontrolle und Datenschutz

Die Kontrolle über persönliche Daten und Konversationsverläufe ist ein grundlegendes Recht und eine wesentliche
Anforderung an Datenschutz und Compliance (revDSG, DSGVO). Ohne diese Kontrolle entstehen Vertrauensverluste.

### Mehrwert und Nutzen: Regulatorische Sicherheit und erhöhtes Nutzervertrauen

Für C-Level-Führungskräfte garantiert die nutzerzentrierte Datenkontrolle die Einhaltung strenger Datenschutzrichtlinien
und minimiert rechtliche Risiken. Dies stärkt das Vertrauen der Mitarbeitenden in die KI-Systeme und fördert eine
verantwortungsbewusste Nutzung. IT- und Compliance-Teams profitieren von integrierten Funktionen, die die Wahrung von
Betroffenenrechten wie Auskunfts- oder Löschbegehren effizient unterstützen und den administrativen Aufwand reduzieren.

### Konzepte & Prozesse: Granulare Verwaltung und konfigurierbare Aufbewahrung

Benutzer verfügen über granulare Verwaltungsrechte für ihre gesamte Konversationshistorie. Das System unterstützt die
Einsichtnahme, Reaktivierung und Löschung von einzelnen Chats oder ganzen Profilen. Die zugrunde liegende Architektur
ermöglicht zudem eine konfigurierbare Datenaufbewahrung, um regulatorischen und internen Richtlinien gerecht zu werden.
Jede Aktion wird revisionssicher im Audit-Trail erfasst.

### Technische Umsetzung im Swiss AI Hub: Thread-Management und DSGVO-APIs

Der Dienst **Thread-Verwaltung** ermöglicht Benutzern, alle ihre vergangenen Konversations-Threads anzuzeigen, zu suchen
und zu filtern. Konversationen können archiviert, mit anderen geteilt oder geklont werden. Benutzer haben die
Möglichkeit, frühere Nachrichten zu bearbeiten, Nachrichten zu löschen oder Antworten neu zu generieren. Einzelne
Konversationen können gelöscht werden. Die Plattform unterstützt das **Recht auf Löschung (Art. 17 DSGVO / Art. 32
revDSG)** durch Funktionen wie das Entfernen von Nutzern aus Threads; ephemere Daten werden nach 30 Tagen automatisch
gelöscht. Für die permanente Datenspeicherung müssen Organisationen eigene Daten-Lifecycle-Richtlinien implementieren,
und auch Trace-Aufbewahrungsrichtlinien sind konfigurierbar. APIs für Benutzerprofile, Konversations-Threads und
Audit-Logs sind verfügbar, um Auskunftsrechten nachzukommen. Die PII-Anonymisierung mittels Presidio (gemäss Kapitel 07)
schützt zusätzlich sensible Daten im Fluss.
`UNKLARHEIT IN DER DOKU - BITTE PRÜFEN: Eine explizite Funktion zum Exportieren oder Ausdrucken von Chat-Verläufen ist in der Quelldokumentation der UI-Sektion nicht direkt aufgeführt, wird aber durch die Verfügbarkeit von APIs für Audit-Logs und Threads impliziert. Die explizite Funktion zum Löschen des gesamten Profils wird nicht beschrieben, kann aber über administrative Dienste erfolgen.`

## 5. Lokalisierung und Mehrsprachigkeit für den Schweizer Markt

Die Viersprachigkeit der Schweiz ist ein einzigartiges Merkmal, das bei der Entwicklung von Unternehmenssoftware
berücksichtigt werden muss. Eine mangelnde Lokalisierung kann zu Akzeptanzproblemen und einer ungleichen Nutzererfahrung
führen.

### Mehrwert und Nutzen: Breite Akzeptanz und vereinfachte Einführung

Für Führungskräfte sichert die umfassende Mehrsprachigkeit eine breitere Akzeptanz der Plattform in allen Schweizer
Sprachregionen, was die Benutzerfreundlichkeit erhöht und die Einführung von KI-Lösungen beschleunigt. Insbesondere für
Schweizer Institutionen des öffentlichen Sektors ist die Bereitstellung von Dienstleistungen in mehreren Landessprachen
eine Grundvoraussetzung, die ohne kundenspezifische Entwicklung erfüllt wird. IT-Teams profitieren von einer
einheitlichen Plattforminstanz, die für verschiedene Sprachgemeinschaften nutzbar ist und die Komplexität der
Bereitstellung reduziert.

### Konzepte & Prozesse: Vier Landessprachen und dynamische Anpassung

Die Plattform unterstützt die vier Landessprachen der Schweiz: Deutsch, Englisch, Französisch und Italienisch. Die
gesamte Benutzeroberfläche, einschliesslich Navigation, Fehlermeldungen und Hilfetexte, ist übersetzt. Benutzer können
ihre bevorzugte Sprache wählen, die über Sitzungen hinweg bestehen bleibt. Dynamisch generierte Inhalte wie
Dienstleistungsbeschreibungen und Agentennamen passen sich ebenfalls an die gewählte Sprache an. Das System kann zudem
die Dokumentsprache für die Verarbeitung und das Wissensmanagement automatisch erkennen, was sprachspezifische
Suchoptimierung ermöglicht.

### Technische Umsetzung im Swiss AI Hub: Übersetzungsarchitektur und Schweizerdeutsch

Alle benutzernahen Texte sind übersetzt, wobei Deutsch als Standardsprache dient, falls eine Übersetzung fehlt. Die
**Übersetzungsqualität** wird durch konsistente Terminologie über alle Sprachen hinweg gewährleistet. Benutzerdefinierte
Ressourcen wie Wissens-Namespaces, Datenbanknamen und Ordnerbeschreibungen können Übersetzungen für alle unterstützten
Sprachen enthalten. Die **Spracheingabe unterstützt Schweizerdeutsch**, neben Deutsch und Englisch, und KI-Antworten
können auch als Sprache ausgegeben werden. Zahlen, Daten, Zeiten und Währungen werden gemäss den regionalen Konventionen
formatiert. Die Suchfunktionalität verwendet sprachspezifische Tokenisierung und Stemming, um präzise Ergebnisse in
jeder Sprache zu liefern. Organisationen können zudem benutzerdefinierte Übersetzungen für unternehmensspezifische
Begriffe hinzufügen.
