# Kapitel 09: Regulatorische Compliance

Die Einführung von künstlicher Intelligenz in Schweizer Unternehmen ist untrennbar mit der Einhaltung strenger
gesetzlicher Vorgaben verbunden. Mit dem Inkrafttreten des revidierten Datenschutzgesetzes (revDSG) am 1. September
2023, der extraterritorialen Wirkung der europäischen DSGVO (GDPR) sowie der schrittweisen Umsetzung des EU AI Acts
stehen Organisationen vor einer komplexen Compliance-Landschaft. Ein KI-System darf in diesem Umfeld keine juristische
«Black Box» sein, sondern muss als prüfbarer Bestandteil der Corporate Governance fungieren.

Dieses Kapitel legt dar, wie der Swiss AI Hub regulatorische Anforderungen nicht durch bürokratische Hürden, sondern
durch integrierte Architektur-Merkmale löst. Die Plattform transformiert Compliance von einem manuellen Kontrollaufwand
in einen automatisierten Standardprozess, der rechtliche Risiken minimiert und die notwendige Transparenz für interne
und externe Auditoren schafft.

## Auf einen Blick

- **Territoriale Rechtskonformität:** Durch isolierte Betriebsmodelle und lokale Datenhaltung verbleiben sensible
  Informationen im schweizerischen Rechtsraum und unterstehen ausschliesslich dem revDSG.
- **Privacy by Design:** Automatisierte Daten-Lebenszyklen und konfigurierbare Löschfristen verankern den Datenschutz
  tief in der technischen Architektur der Wissensdatenbanken.
- **Konformität mit dem EU AI Act:** Die Plattform unterstützt die regulatorischen Anforderungen für Hochrisiko-Systeme
  durch Transparenzmechanismen, Rückverfolgbarkeit und zwingende menschliche Aufsicht.
- **Automatisierte Betroffenenrechte:** Integrierte APIs zur Umsetzung von Auskunfts- und Löschbegehren (DSAR)
  reduzieren den administrativen Aufwand und sichern die gesetzlichen Fristen.
- **Inklusivität durch Mehrsprachigkeit:** Die native Unterstützung der Schweizer Landessprachen gewährleistet den
  diskriminierungsfreien Zugang und erfüllt die Anforderungen des Service Public.

## Territoriale Rechtskonformität und Datensouveränität

### Geschäftlicher Nutzen

Für Schweizer Organisationen, insbesondere in der öffentlichen Verwaltung, im Gesundheitswesen und im Finanzsektor, ist
der physische Standort der Daten entscheidend. Die Nutzung globaler Cloud-Dienste kollidiert oft mit dem Risiko, dass
Daten gemäss ausländischem Recht (z.B. US CLOUD Act) abgegriffen werden könnten. Um Konflikte mit dem revDSG und der
DSGVO zu vermeiden, benötigen Unternehmen die Garantie, dass sensible Daten den schweizerischen Rechtsraum niemals
verlassen. Eine souveräne Infrastruktur erleichtert Audit-Prozesse massiv und stärkt das Vertrauen von Bürgern und
Kunden in die digitale Integrität der Organisation.

### Konzeptioneller Ansatz

Der Swiss AI Hub löst das Problem internationaler Datentransfers durch das Prinzip der absoluten Datensouveränität. Da
die Plattform vollständig in der Infrastruktur des Kunden betrieben wird, entfällt die Notwendigkeit für komplexe
rechtliche Konstrukte wie Standardvertragsklauseln (SCCs) für Datentransfers in unsichere Drittstaaten. Das Konzept
unterstützt isolierte Betriebsmodelle, bei denen Wissen lokal verarbeitet wird. Durch den EU-Angemessenheitsbeschluss
für die Schweiz ist zudem der Datenverkehr mit europäischen Partnern rechtlich abgesichert, solange die Datenhoheit
innerhalb der definierten Perimeter gewahrt bleibt.

### Technische Umsetzung im Swiss AI Hub

Die Plattform ermöglicht verschiedene Deployment-Szenarien zur Wahrung der territorialen Integrität. Im
On-Premise-Betrieb oder in einer Schweizer Private Cloud verbleiben sämtliche Datenbanken und Vektorspeicher unter der
direkten Kontrolle des Mandanten. Für höchste Sicherheitsstufen unterstützt das System Air-Gap-Installationen, bei denen
die Plattform physisch vom Internet getrennt ist. Hierbei kommen lokal gehostete Modelle via vLLM oder llama.cpp zum
Einsatz, sodass keine API-Aufrufe an externe Anbieter gesendet werden müssen. Dies garantiert technisch, dass kein
einziges Byte den definierten Schweizer Sicherheitsperimeter verlässt.

## Datenschutz und Automatisierung von Betroffenenrechten

### Geschäftlicher Nutzen

Das revDSG und die DSGVO gewähren Einzelpersonen weitreichende Rechte, darunter Auskunft über gespeicherte Daten,
Berichtigung und Löschung. Unter dem Schweizer revDSG können Verstösse gegen diese Pflichten zu persönlichen Bussen für
Verantwortliche von bis zu CHF 250'000 führen. Die manuelle Bearbeitung solcher Anfragen (Data Subject Access Requests,
DSAR) innerhalb der gesetzlichen Frist von 30 Tagen ist zeitaufwändig und fehleranfällig. Eine Enterprise-Lösung muss
diese Prozesse standardisieren, um den administrativen Aufwand zu reduzieren und Compliance-Verstösse durch menschliches
Versagen auszuschliessen.

### Konzeptioneller Ansatz

Die Plattform verankert «Privacy by Design» durch ein striktes Lebenszyklus-Management. Das Konzept unterscheidet
zwischen flüchtigen Interaktionsdaten und permanentem Wissen in der Wissensdatenbank. Durch konfigurierbare
Aufbewahrungsrichtlinien (Retention Policies) reinigt sich das System selbstständig. Zudem sind Mechanismen vorhanden,
um Personenidentifizierbare Informationen (PII) auf Anfrage gezielt zu identifizieren, zu korrigieren oder
unwiderruflich zu entfernen. Dies stellt sicher, dass die Datenminimierung kein Lippenbekenntnis bleibt, sondern
technisch erzwungen wird.

### Technische Umsetzung im Swiss AI Hub

Technisch werden diese Anforderungen durch automatische Ablaufmechanismen und administrative APIs umgesetzt:

- **Ephemere Daten:** Caches und Sitzungsdaten im Arbeitsspeicher (Valkey/Redis) besitzen eine harte Lebensdauer (TTL)
  von 30 Tagen.
- **Workflow-Ereignisse:** Event-Logs in NATS JetStream unterliegen doppelten Beschränkungen – sie werden nach 30 Tagen
  oder beim Erreichen von 10 Millionen Nachrichten automatisch rotiert.
- **DSAR-Unterstützung:** Über die Benutzerprofil-API können Datenkopien für das Auskunftsrecht (Art. 25 revDSG)
  exportiert werden. Administratoren können Profile aktualisieren (Berichtigung) oder Nutzer aus Konversations-Threads
  entfernen (Löschung). Da Audit-Logs revisionssicher bleiben müssen, werden PII dort bei Löschbegehren pseudonymisiert,
  während der operative Zugriff entzogen wird.

## Konformität mit dem EU AI Act und ethische Governance

### Geschäftlicher Nutzen

Mit dem Inkrafttreten des EU AI Acts im August 2024 entsteht ein globaler Massstab für die Regulierung von KI. Schweizer
Unternehmen, die im EU-Markt agieren oder Hochrisiko-Anwendungen (z.B. in der Personalrekrutierung oder Kreditprüfung)
einsetzen, müssen Transparenz, menschliche Aufsicht und Risikomanagement nachweisen. Die Nichteinhaltung kann nicht nur
horrende Strafen nach sich ziehen, sondern auch den Marktzugang gefährden. Eine gesetzeskonforme Plattform schützt die
Investitionen, indem sie die notwendigen Dokumentations- und Kontrollfunktionen bereits im Kern bereitstellt.

### Konzeptioneller Ansatz

Der Swiss AI Hub ist darauf ausgelegt, die Anforderungen für verschiedene Risikoklassen des AI Acts zu erfüllen. Das
zentrale Element ist die Erklärbarkeit: Es muss jederzeit nachvollziehbar sein, auf welcher Datenbasis eine Antwort
generiert wurde. Für kritische Entscheidungen implementiert die Plattform das Prinzip «Human-in-the-Loop». Dies stellt
sicher, dass eine Maschine niemals ohne menschliche Letztentscheidung in sensiblen Kontexten agiert, was auch die
Anforderungen des revDSG an das Hochrisikoprofiling abdeckt.

### Technische Umsetzung im Swiss AI Hub

Die Plattform bietet spezifische Werkzeuge zur Erfüllung der regulatorischen Pflichten:

- **Transparenz und Tracing:** Durch Phoenix-Tracing und Quellenzuordnung wird jede Antwort mit ihren
  Ursprungsdokumenten in der Wissensdatenbank verknüpft, was Halluzinationen offenlegt.
- **Human-in-the-Loop:** Die Workflow-Engine unterstützt Unterbrechungspunkte (`HumanInTheLoopEvents`), an denen ein
  Prozess stoppt, bis ein autorisierter Benutzer das Ergebnis prüft. Alternativ ermöglicht «Bot-in-the-Loop» die
  Eskalation via Slack oder Teams.
- **Auditierung:** Lückenlose Logs aller Interaktionen und die Versionierung von Agenten-Profilen erlauben es Auditoren,
  exakt zu rekonstruieren, welches Modell zu welchem Zeitpunkt mit welchen Daten gearbeitet hat. Dies unterstützt die
  Erstellung von Datenschutz-Folgenabschätzungen (DPIA).

## Inklusivität und Schweizer Mehrsprachigkeit

### Geschäftlicher Nutzen

Für Institutionen in der Schweiz ist Mehrsprachigkeit eine gesetzliche Pflicht. Eine Compliance-Plattform muss
sicherstellen, dass Mitarbeitende und Bürger in allen Sprachregionen gleichberechtigten Zugang zu KI-Diensten haben.
Diskriminierung durch Sprachbarrieren widerspricht dem Service Public und internen Diversitätsrichtlinien. Zudem müssen
regulatorische Dokumentationen und Benutzerhinweise in den Landessprachen vorliegen, um die Transparenzanforderungen
(Art. 19 revDSG) vollumfänglich zu erfüllen.

### Konzeptioneller Ansatz

Internationalisierung ist als Kernfunktion verankert. Das Konzept sieht vor, dass alle vier Landessprachen (Deutsch,
Französisch, Italienisch, Englisch) gleichberechtigt behandelt werden. Dies betrifft nicht nur die Benutzeroberfläche,
sondern auch die semantische Verarbeitung. Ein Agenten-Profil muss in der Lage sein, Dokumente in einer Sprache zu
verstehen und Fragen in einer anderen Sprache präzise zu beantworten, ohne an Qualität zu verlieren.

### Technische Umsetzung im Swiss AI Hub

Die Umsetzung erfolgt durchgängig auf allen Ebenen:

- **Lokalisierte UI:** Sämtliche Menüs, Fehlermeldungen und Hilfetexte sind vollständig übersetzt. Die Sprachwahl wird
  im Profil des Benutzers gespeichert.
- **Sprachspezifische Suche:** Die Ingestion-Pipeline und die Vektordatenbank unterstützen sprachspezifische
  Tokenisierung und Stemming für alle vier Sprachen. Dies stellt sicher, dass Suchanfragen beispielsweise in Italienisch
  auch relevante italienische Dokumente finden.
- **Regionale Formatierung:** Zahlen, Daten und Währungen werden automatisch gemäss den Schweizer Konventionen
  formatiert, was die Korrektheit der Datenrepräsentation über Sprachgrenzen hinweg sichert.
