# Kapitel 09: Regulatorische Compliance

Die Einführung von künstlicher Intelligenz in Schweizer Unternehmen ist untrennbar mit der Einhaltung strenger
gesetzlicher Vorgaben verbunden. Mit dem Inkrafttreten des revidierten Datenschutzgesetzes (revDSG) am 1. September
2023, der extraterritorialen Wirkung der europäischen DSGVO (GDPR) sowie der schrittweisen Einführung des EU AI Acts
stehen Organisationen vor einer komplexen Compliance-Landschaft. Ein KI-System darf keine juristische «Black Box» sein.

Dieses Kapitel legt dar, wie der Swiss AI Hub regulatorische Anforderungen nicht durch bürokratische Hürden, sondern
durch integrierte Architektur-Features löst. Die Plattform transformiert Compliance von einem manuellen Aufwand in einen
automatisierten Standardprozess, der Risiken minimiert und Rechtssicherheit schafft.

## Auf einen Blick

- **Territoriale Rechtskonformität:** Durch isolierte Betriebsmodelle und lokale Datenhaltung wird sichergestellt, dass
  sensible Daten den schweizerischen Rechtsraum niemals verlassen.
- **Privacy by Design:** Automatisierte Lebenszyklen für Daten (z.B. harte 30-Tage-Löschfristen für Caches) verankern
  den Datenschutz tief in der technischen Architektur.
- **Human-in-the-Loop:** Die Workflow-Engine erzwingt bei kritischen Entscheidungen technisch eine menschliche Freigabe,
  um den Anforderungen des EU AI Acts und des revDSG (Hochrisikoprofiling) zu genügen.
- **Automatisierte Betroffenenrechte:** APIs und Prozesse zur Umsetzung von Auskunfts- und Löschbegehren reduzieren den
  administrativen Aufwand für DSAR-Anfragen drastisch.
- **Native Mehrsprachigkeit:** Die Plattform unterstützt die vier Schweizer Landessprachen nicht nur in der Oberfläche,
  sondern auch in der semantischen Verarbeitung, um Diskriminierung auszuschliessen.

## Territoriale Rechtskonformität und Datensouveränität

### Geschäftlicher Nutzen

Für Schweizer Organisationen, insbesondere im Gesundheitswesen, der öffentlichen Verwaltung und der Finanzindustrie, ist
der physische Standort der Daten oft entscheidend. Die Nutzung globaler Cloud-Dienste kollidiert häufig mit internen
Richtlinien oder dem Risiko, dass Daten gemäss dem US CLOUD Act abgegriffen werden könnten. Um Konflikte mit dem revDSG
und der DSGVO zu vermeiden, benötigen Unternehmen die Garantie, dass sensible Daten den schweizerischen Rechtsraum
niemals verlassen. Eine solche Garantie erleichtert Audit-Prozesse massiv und stärkt das Vertrauen von Kunden und
Bürgern.

### Konzeptioneller Ansatz

Der Swiss AI Hub löst das Problem internationaler Datentransfers durch das Prinzip der absoluten Datensouveränität. Da
die Plattform vollständig in der Infrastruktur des Kunden betrieben wird, entfällt die Notwendigkeit komplexer
rechtlicher Konstrukte wie Standardvertragsklauseln (SCCs) für Datentransfers in unsichere Drittstaaten. Das Konzept
unterstützt isolierte Betriebsmodelle, bei denen Daten lokal verarbeitet werden und somit ausschliesslich dem Schweizer
Recht unterstehen. Durch den EU-Angemessenheitsbeschluss für die Schweiz ist zudem der Datenverkehr mit europäischen
Partnern rechtlich abgesichert, solange die Daten in der Schweiz verbleiben.

### Technische Umsetzung im Swiss AI Hub

Die Plattform ermöglicht verschiedene Deployment-Szenarien zur Wahrung der territorialen Integrität. Im
**On-Premise-Betrieb** oder in einer **Schweizer Private Cloud** verbleiben alle Datenbanken und Vektorspeicher unter
der direkten Kontrolle des Mandanten. Für höchste Sicherheitsstufen unterstützt das System **Air-Gap-Installationen**,
bei denen die Plattform physisch vom Internet getrennt ist. Hierbei kommen lokal gehostete Modelle (via vLLM oder
llama.cpp) zum Einsatz, sodass keine API-Aufrufe an externe Anbieter gesendet werden müssen. Dies garantiert technisch,
dass kein einziges Byte den definierten Sicherheitsperimeter verlässt.

## Automatisierung von Betroffenenrechten und Datenschutz

### Geschäftlicher Nutzen

Das revDSG und die DSGVO gewähren Einzelpersonen weitreichende Rechte, darunter Auskunft über gespeicherte Daten,
Berichtigung und Löschung. Die Missachtung dieser Pflichten kann insbesondere unter dem Schweizer revDSG zu persönlichen
Bussen für Verantwortliche von bis zu CHF 250'000 führen. Die manuelle Bearbeitung solcher Anfragen (Data Subject Access
Requests, DSAR) ist zeitaufwändig und fehleranfällig. Eine Enterprise-Lösung muss diese Prozesse standardisieren, um den
administrativen Aufwand zu reduzieren und Compliance-Verstösse durch menschliches Versagen oder verpasste Fristen
auszuschliessen.

### Konzeptioneller Ansatz

Die Plattform verankert «Privacy by Design» tief in ihrer Datenarchitektur. Anstatt Daten unbegrenzt zu horten,
implementiert das System ein striktes Lebenszyklus-Management. Das Konzept unterscheidet zwischen flüchtigen
Interaktionsdaten und permanentem Wissen. Durch konfigurierbare Aufbewahrungsrichtlinien (Retention Policies) reinigt
sich das System selbstständig. Zudem sind Mechanismen vorhanden, um spezifische Personendaten auf Anfrage gezielt zu
identifizieren und unwiderruflich zu entfernen, ohne die Integrität des Gesamtsystems zu gefährden.

### Technische Umsetzung im Swiss AI Hub

Technisch werden diese Anforderungen durch automatische Ablaufmechanismen und APIs umgesetzt:

- **Ephemere Daten:** Caches und Sitzungsdaten im Hochleistungs-Speicher (Redis) besitzen eine harte Lebensdauer (TTL)
  von 30 Tagen und werden danach automatisch gelöscht.
- **Workflow-Ereignisse:** Event-Logs (in NATS JetStream) unterliegen doppelten Beschränkungen – sie werden entweder
  nach 30 Tagen oder beim Erreichen von Speichergrenzen (z.B. 10 Millionen Nachrichten) rotiert.
- **Betroffenenrechte:** Über administrative APIs können Benutzerprofile aktualisiert (Recht auf Berichtigung) oder
  Nutzer aus Konversations-Threads entfernt werden (Recht auf Löschung). Da Audit-Logs aus Revisionsgründen
  unveränderlich bleiben müssen, werden persönliche Referenzen dort pseudonymisiert, während der operative Zugriff auf
  die Daten entzogen wird.

## Konformität mit dem EU AI Act und ethische KI

### Geschäftlicher Nutzen

Mit dem EU AI Act tritt eine umfassende Regulierung in Kraft, die auch für Schweizer Unternehmen relevant ist, die im
EU-Markt agieren. Das Gesetz sowie das Schweizer revDSG (im Bereich Hochrisikoprofiling) fordern für sensible Bereiche
Transparenz, menschliche Aufsicht und Risikomanagement. Unternehmen müssen nachweisen können, dass ihre KI-Systeme keine
undurchsichtige «Black Box» sind, sondern erklärbare Entscheidungen treffen. Die Nichteinhaltung kann zu massiven
Sanktionen führen und den Marktzugang gefährden.

### Konzeptioneller Ansatz

Der Swiss AI Hub ist darauf ausgelegt, die Anforderungen für Hochrisiko-Systeme und Systeme mit begrenztem Risiko zu
unterstützen. Das zentrale Element ist die Transparenz: Es muss jederzeit klar sein, dass ein Nutzer mit einer KI
interagiert (Kennzeichnungspflicht) und auf welcher Basis eine Antwort generiert wurde. Für kritische Entscheidungen
implementiert die Plattform das Prinzip «Human-in-the-Loop», das sicherstellt, dass eine Maschine niemals ohne
menschliche Letztentscheidung in sensiblen Kontexten agiert.

### Technische Umsetzung im Swiss AI Hub

Die Plattform bietet spezifische Werkzeuge zur Erfüllung dieser regulatorischen Pflichten:

- **Transparenz und Kennzeichnung:** Durch Tracing (Phoenix) und Quellenzuordnung wird jede generierte Antwort mit ihren
  Ursprungsdokumenten verknüpft, was Halluzinationen offenlegt und Erklärbarkeit schafft.
- **Menschliche Aufsicht:** Die Workflow-Engine unterstützt Unterbrechungspunkte (`HumanInTheLoopEvents`), an denen ein
  Prozess stoppt, bis ein autorisierter menschlicher Benutzer das Ergebnis prüft und freigibt. Dies ist essenziell für
  Anwendungsfälle wie Kreditvergaben oder HR-Entscheidungen, die unter das Verbot automatisierter Einzelentscheidungen
  fallen könnten.
- **Audit-Logging:** Durch lückenloses Logging aller Interaktionen und die Versionierung von Agenten-Profilen lässt sich
  für Regulatoren exakt rekonstruieren, welches Modell und welche Datenbasis zu einem bestimmten Zeitpunkt verwendet
  wurden.

## Inklusivität und Schweizer Mehrsprachigkeit

### Geschäftlicher Nutzen

Für den öffentlichen Sektor und landesweit tätige Unternehmen in der Schweiz ist Mehrsprachigkeit keine Option, sondern
eine gesetzliche und kulturelle Pflicht. Eine Compliance-Plattform muss sicherstellen, dass Bürger und Mitarbeiter in
der Deutschschweiz, der Romandie und im Tessin gleichberechtigten Zugang zu Informationen und Dienstleistungen haben.
Diskriminierung durch Sprachbarrieren widerspricht dem Service Public und internen Diversitätsrichtlinien.

### Konzeptioneller Ansatz

Internationalisierung ist im Kern der Plattform verankert, nicht als nachträgliche Übersetzungsschicht. Das Konzept
sieht vor, dass alle vier Landessprachen (Deutsch, Französisch, Italienisch, Englisch) als gleichberechtigt behandelt
werden. Dies betrifft nicht nur die statische Benutzeroberfläche, sondern auch die dynamische Verarbeitung der Inhalte.
Ein KI-Agent muss in der Lage sein, ein französisches Dokument zu verstehen und eine deutsche Frage dazu korrekt zu
beantworten, ohne an Qualität zu verlieren.

### Technische Umsetzung im Swiss AI Hub

Die Umsetzung erfolgt durchgängig auf allen Ebenen der Architektur:

- **Lokalisierte UI:** Alle Menüs, Fehlermeldungen und Hilfetexte sind vollständig lokalisiert. Die Sprachwahl wird im
  Benutzerprofil gespeichert und über Sitzungen hinweg beibehalten.
- **Sprachspezifische Suche:** Die Ingestion-Pipeline und die Vektordatenbank unterstützen sprachspezifische
  Tokenisierung und Stemming. Dies stellt sicher, dass Suchanfragen in italienischer Sprache auch relevante italienische
  Dokumente finden, indem sprachspezifische Stammformen berücksichtigt werden.
- **Dynamische Generierung:** Agenten passen ihre Ausgabesprache dynamisch an die Präferenz des Benutzers an. Fehlen
  Übersetzungen für spezifische Fachbegriffe, greift das System auf Deutsch als Standardsprache zurück, um
  Funktionalität zu gewährleisten.
