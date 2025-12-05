# Die Business-Herausforderung: KI im Unternehmen

## Die Illusion der Einfachheit und die Infrastrukturlücke

Die aktuelle Wahrnehmung von künstlicher Intelligenz ist oft verzerrt durch die Leichtigkeit des Einstiegs. Mit modernen
Frameworks wie LangChain oder LlamaIndex können Entwickler innerhalb weniger Stunden beeindruckende Prototypen
erstellen. Diese Zugänglichkeit täuscht jedoch über eine fundamentale Diskrepanz hinweg: Es besteht ein massiver
Unterschied zwischen einer funktionierenden Tech-Demo und einem belastbaren Enterprise-System. Sobald ein KI-Prototyp
den geschützten Raum der Entwicklung verlässt, entstehen komplexe Anforderungen, die nichts mit der eigentlichen
KI-Logik zu tun haben, sondern reine Infrastrukturthemen betreffen. Unternehmen stehen vor der Herausforderung,
Benutzerauthentifizierung, Skalierung, Monitoring und Kostenkontrolle integrieren zu müssen. Werden diese Aspekte
vernachlässigt, bleibt das Projekt im Stadium eines Experimentes stecken oder wird zu einem unkalkulierbaren
Sicherheitsrisiko.

Dies führt zur sogenannten Infrastrukturlücke. Organisationen müssen sich entscheiden, ob sie eine komplexe
Infrastruktur von Grund auf neu bauen – was wertvolle Entwicklerressourcen bindet – oder sich in die Abhängigkeit
grosser Cloud-Provider begeben. Der Swiss AI Hub löst dieses Dilemma, indem er die notwendige Infrastruktur als Produkt
bereitstellt. Anstatt dass Teams Basisfunktionen wie Zugriffskontrollen oder Audit-Trails immer wieder neu
programmieren, liefert die Plattform diese Komponenten als standardisierte Module. Dies ermöglicht den Fokus auf die
geschäftliche Logik, während die notwendige IT-Basis bereits produktionsbereit zur Verfügung steht. Technisch wird dies
durch eine containerisierte Architektur realisiert, die mittels Docker Compose oder Kubernetes orchestriert wird und
Dienste wie NATS für das Messaging und automatische Service Discovery bereits integriert hat.

## Das «Day 2»-Problem und die Betriebskosten

Der wahre Aufwand von KI-Projekten offenbart sich oft erst am «Tag 2» – dem Beginn des regulären Betriebs. Während die
initialen Kosten für die Entwicklung eines Chatbots überschaubar sein mögen, explodieren die Aufwände oft durch fehlende
Governance-Strukturen im laufenden Betrieb. Ohne zentrale Steuerung entstehen fragmentierte Landschaften: Eine Abteilung
nutzt Kreditkarten für OpenAI-APIs, eine andere baut isolierte Systeme auf lokalen Servern, und die Finanzabteilung
verliert jeglichen Überblick über die kumulierten Kosten. Diese Fragmentierung führt nicht nur zu ineffizienten
Ausgaben, sondern auch zu technischen Schulden, da Wissen in Silos gefangen bleibt und Sicherheitsrichtlinien nicht
einheitlich durchgesetzt werden können.

Um diesem Wildwuchs zu begegnen, etabliert der Swiss AI Hub eine zentrale Instanz für Governance und Betrieb. Die
Plattform transformiert fragmentierte Einzellösungen in eine einheitliche Strategie. Durch technische Komponenten wie
das integrierte LLM-Gateway (implementiert durch LiteLLM) werden Kosten transparent über alle Modelle hinweg getrackt.
Budgets können auf Team- oder Benutzerebene durchgesetzt werden, und automatische Stopps verhindern unerwartete
Budgetüberschreitungen. Gleichzeitig sorgt die Integration von Unternehmensauthentifizierung (SSO/OAuth) dafür, dass
jeder Zugriff – ob durch einen Benutzer oder einen technischen Prozess – verifiziert und protokolliert wird.

## Schweizer Compliance und die Datenhoheit

Für Schweizer Unternehmen und die öffentliche Verwaltung stellt die Nutzung globaler KI-Dienste eine besondere Hürde
dar. Datenschutzgesetze und interne Compliance-Vorgaben verbieten es oft, Unternehmensdaten – seien es Personendaten
oder geistiges Eigentum – an Server ausserhalb der eigenen Rechtshoheit oder gar ausserhalb des eigenen Rechenzentrums
zu senden. Dies führt häufig dazu, dass KI-Initiativen von der Rechtsabteilung oder der IT-Security blockiert werden.
Die Herausforderung besteht darin, die Leistungsfähigkeit moderner Sprachmodelle zu nutzen, ohne die Kontrolle über den
Datenfluss aufzugeben.

Der Swiss AI Hub löst dieses Dilemma durch strikte Datensouveränität und granulare Kontrolle über den Datenfluss. Die
Plattformarchitektur erlaubt es, die Datenverarbeitung exakt an das Risikoprofil anzupassen:

- **Vollständige On-Premise-Bereitstellung:** Sensible Daten verlassen niemals das eigene Netzwerk; lokale Modelle wie
  Mistral oder DeepSeek übernehmen die Verarbeitung, unterstützt durch lokale Vektordatenbanken wie Milvus.
- **Schweizer Cloud-Bereitstellung:** Nutzung zertifizierter Schweizer Rechenzentren für maximale Rechtssicherheit bei
  reduzierter eigener Hardware-Last.
- **Hybride Ansätze:** Unkritische Anfragen nutzen leistungsstarke globale Cloud-Modelle, während vertrauliche Dokumente
  strikt lokal verarbeitet werden.

Zusätzlich sorgt die Daten-zu-Wissen-Pipeline mit Tools wie Docling für das sichere Parsing und Chunking interner
Dokumente, während Presidio automatisch PII (Personenidentifizierbare Informationen) erkennt und maskiert, bevor diese
verarbeitet werden.

## Von der Black Box zur prüfbaren Transparenz

Ein weiteres Kernproblem beim Einsatz generativer KI im Unternehmenskontext ist das mangelnde Vertrauen in die
Entscheidungsfindung der Modelle («Black Box»). In regulierten Branchen ist es inakzeptabel, wenn ein System
Entscheidungen trifft, die nicht nachvollziehbar sind, oder wenn unklar ist, auf welcher Datenbasis eine Antwort
generiert wurde. Offene Agenten-Systeme, die autonom agieren und deren Verhalten schwer vorhersehbar ist, stellen
hierbei ein unkalkulierbares Risiko dar. Um Compliance-Anforderungen gerecht zu werden, müssen Prozesse deterministisch
und auditierbar sein.

Der Swiss AI Hub setzt hier auf das Prinzip der geschlossenen Workflows (Closed Workflows) anstelle offener Schleifen.
Ein Agenten-Bauplan definiert explizite Pfade, die bestimmen, welche Aktionen erlaubt sind. Technisch wird dies durch
eine umfassende Observability auf vier Ebenen realisiert: Vom Infrastruktur-Monitoring über die Ausführungsverfolgung
mittels Phoenix bis hin zur Pipeline-Überwachung via Dagster wird jede Interaktion transparent gemacht. Dies schafft die
notwendige «Trust equation»: Vorhersagbarkeit plus Sichtbarkeit plus Kontrolle ergibt Vertrauen. Jede Entscheidung ist
beweisbar, jeder Datenzugriff protokolliert und durch das SDK deterministisch testbar.
