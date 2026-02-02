# Die Business-Herausforderung – AI im Unternehmen

Der aktuelle Hype um generative KI verdeckt oft eine unbequeme Wahrheit: Es ist trivial, an einem Nachmittag eine
beeindruckende Demo zu erstellen, aber ausserordentlich schwierig, ein produktives, unternehmenstaugliches System zu
bauen. Viele Organisationen befinden sich aktuell in einer Phase der Desillusionierung. Nach erfolgreichen ersten Tests
mit Bibliotheken wie LangChain oder direkten API-Aufrufen an OpenAI stellen sie fest, dass der Weg zur Produktivsetzung
durch massive infrastrukturelle Hürden blockiert ist.

Dieses Kapitel analysiert die Diskrepanz zwischen Prototyping und Engineering und beleuchtet die spezifischen
Herausforderungen für Schweizer Unternehmen. Es zeigt auf, warum der Versuch, KI-Infrastruktur selbst zu bauen, oft in
einer teuren Sackgasse endet und wie die Lücke zwischen dem ersten «Wow»-Effekt und einem stabilen Betrieb («Day 2»)
durch einen produktorientierten Infrastruktur-Ansatz geschlossen werden kann.

## Auf einen Blick

- **Infrastruktur-Lücke:** Der Schritt vom Prototyp zur Produktion scheitert meist nicht an der KI-Logik, sondern an
  fehlenden Enterprise-Funktionen wie Authentifizierung, Monitoring und Skalierbarkeit.
- **Schatten-IT und Fragmentierung:** Isolierte KI-Experimente in Fachabteilungen erzeugen Datensilos und
  unkontrollierbare Kosten, die eine zentrale Governance verunmöglichen.
- **Schweizer Datensouveränität:** Strenge regulatorische Anforderungen blockieren oft die Nutzung ausländischer
  Cloud-Dienste, was ohne lokale Alternativen zu einem Innovationsstau führt.
- **Investitionsschutz:** Offene Standards und eine modell-agnostische Architektur verhindern einen Vendor-Lock-in und
  sichern die langfristige technologische Unabhängigkeit.
- **Vertrauen durch Vorhersagbarkeit:** Für geschäftskritische Prozesse sind deterministische Abläufe («Closed
  Workflows») zwingend, um das Risiko unkontrollierter KI-Entscheidungen zu eliminieren.

## Die Infrastrukturlücke: Von der Demo zur Realität

### Geschäftlicher Nutzen

Ein funktionierender Prototyp beantwortet selten die Fragen, die für den operativen Betrieb entscheidend sind: Wie
skalieren wir die Lösung? Wo bleiben unsere Daten physisch? Wie kontrollieren wir die laufenden Kosten? Für
Entscheidungsträger bedeutet diese Lücke ein hohes finanzielles und operatives Risiko. Projekte bleiben oft im
Pilotstadium stecken («Pilot Purgatory»), weil die notwendige Infrastruktur für Sicherheit und Governance fehlt. Dies
führt zu Fehlinvestitionen, da die Time-to-Value durch den nachträglichen, mühsamen Aufbau von Basistechnologien massiv
verzögert wird. IT-Teams binden wertvolle Ressourcen in der Entwicklung von Fundamenten, anstatt geschäftlichen Mehrwert
zu generieren.

### Konzeptioneller Ansatz

Das Kernproblem liegt in der Unterscheidung zwischen KI-Logik und Infrastruktur. Während Code-Bibliotheken beim Bau der
Agenten helfen, ignorieren sie die betriebliche Realität. Eine Enterprise-Lösung benötigt einen «Infrastructure as a
Product»-Ansatz. Das bedeutet, dass Komponenten wie Authentifizierung, Daten-Pipelines und Audit-Trails nicht für jedes
Projekt neu erfunden werden dürfen. Sie müssen als stabile, einsatzbereite Plattform bereitstehen – quasi
«Batteries-included». Nur so lässt sich der Sprung vom «Day 1» (der ersten Demo) zum «Day 2» (dem stabilen Betrieb)
wirtschaftlich und sicher vollziehen.

### Technische Umsetzung im Swiss AI Hub

Der Swiss AI Hub schliesst diese Lücke, indem er die für den Betrieb notwendigen Komponenten integral mitliefert.
Anstatt eigene Lösungen für die Benutzerverwaltung zu entwickeln, nutzen alle Dienste automatisch die Anbindung an den
Identitätsanbieter via SSO/OAuth. Die Plattform bietet eine produktionsreife Architektur, die vom API-Gateway über
Vektordatenbanken (Milvus) bis hin zu skalierbaren Daten-zu-Wissen-Pipelines (Dagster) alles umfasst. Für die operative
Sicherheit sorgt eine integrierte Beobachtbarkeit auf vier Ebenen: Infrastruktur-Monitoring via OpenTelemetry,
Agenten-Tracing via Phoenix, sowie detaillierte Einsichten in Workflow-Events und Datenflüsse.

## Fragmentierung, Schatten-IT und Kostenkontrolle

### Geschäftlicher Nutzen

Ohne eine zentrale Plattform tendieren Abteilungen dazu, isolierte Lösungen zu implementieren. Das Marketing nutzt
ChatGPT-Abos, die IT experimentiert mit Azure OpenAI und die Entwicklung baut lokale RAG-Systeme. Diese Fragmentierung
führt zu intransparenten Kostenstrukturen und fördert eine gefährliche Schatten-IT. Für den CFO wird es unmöglich, die
effektiven Kosten zu ermitteln oder Budgets sinnvoll zuzuweisen. Zudem entstehen Datensilos, in denen wertvolles Wissen
gefangen bleibt. Das Risiko von Compliance-Verstössen steigt mit jeder unkontrollierten Einzellösung, während
Synergieeffekte ungenutzt bleiben.

### Konzeptioneller Ansatz

Die Lösung liegt in der Konsolidierung auf einer mandantenfähigen Plattform, die als zentrales Gateway fungiert. Anstatt
direkter API-Zugriffe auf Modell-Provider durch einzelne Mitarbeitende, läuft jeglicher Verkehr über eine kontrollierte
Instanz. Dies ermöglicht eine zentrale Durchsetzung von Richtlinien, Quotas und Budgets für jeden Mandanten.
Gleichzeitig wird verhindert, dass technologische Sackgassen entstehen, da die zugrundeliegenden Modelle ausgetauscht
werden können, ohne die darüberliegenden Geschäftsprozesse zu beeinträchtigen.

### Technische Umsetzung im Swiss AI Hub

Technisch realisiert der Swiss AI Hub diese Zentralisierung durch das LLM-Gateway (basierend auf LiteLLM). Diese
Komponente abstrahiert die verschiedenen Modell-Provider und ermöglicht ein granulares Kostenmanagement in Echtzeit.
Administratoren können Budgets und Ratenbegrenzungen (Tokens pro Minute) auf Benutzer- oder Team-E Ebene definieren. Die
Plattform verhindert Silos zudem durch zentralisierte Wissensdatenbanken, die über standardisierte Pipelines befüllt
werden. So kann aufbereitetes Wissen organisationsweit sicher wiederverwendet werden, was die Effizienz steigert und die
Kosten pro Anwendungsfall senkt.

## Die Schweizer Compliance-Hürde und Datensouveränität

### Geschäftlicher Nutzen

Spezifisch für Schweizer Organisationen ist die strenge Auslegung von Datenschutz und Datensouveränität. Unternehmen in
regulierten Branchen oder der öffentlichen Verwaltung dürfen sensible Daten oft nicht an Cloud-Dienste im Ausland
übermitteln. Dies führt häufig zu einer Blockadehaltung der IT-Sicherheit: Innovation wird untersagt, weil gängige
SaaS-Lösungen die Anforderungen an die Datenresidenz nicht erfüllen. Unternehmen stehen vor dem Dilemma, entweder auf KI
zu verzichten oder sich in einer rechtlichen Grauzone zu bewegen. Eine souveräne Lösung bricht diesen Kreislauf und
ermöglicht Innovation innerhalb des gesetzlichen Rahmens.

### Konzeptioneller Ansatz

Um dieses Dilemma aufzulösen, muss die Architektur eine flexible Datenhaltung ermöglichen, die sich strikt nach der
Klassifizierung der Daten richtet. Datensouveränität bedeutet hier, dass der Kunde die physische Kontrolle über
Speicherort und Verarbeitung behält. Es muss möglich sein, hochsensible Daten ausschliesslich On-Premise mit lokalen
Modellen zu verarbeiten, während weniger kritische Workloads optional über Schweizer Cloud-Infrastrukturen laufen
können. Der entscheidende Punkt ist, dass der Kunde die Infrastruktur besitzt und kontrolliert, anstatt nur einen Dienst
zu abonnieren.

### Technische Umsetzung im Swiss AI Hub

Der Swiss AI Hub adressiert dies durch seine containerbasierte Architektur, die vollständig in der Infrastruktur des
Kunden betrieben wird – sei es im eigenen Rechenzentrum oder bei einem Schweizer Cloud-Anbieter. Sensible
Unternehmensdaten werden lokal in der Vektordatenbank gespeichert und verarbeitet. Für zusätzliche Sicherheit sorgt die
Integration von Presidio zur automatischen Erkennung und Maskierung von Personenidentifizierbaren Informationen (PII),
noch bevor ein Prompt an ein Modell gesendet wird. Zudem unterstützt die Plattform den Einsatz von Open-Source-Modellen
(wie Mistral oder DeepSeek) via vLLM, sodass eine vollständige «Air-Gapped»-Installation ohne Internetverbindung
realisierbar ist.

## Vertrauen durch Prozess-Stabilität und Transparenz

### Geschäftlicher Nutzen

Ein kritisches Hindernis für den produktiven KI-Einsatz ist die mangelnde Vorhersehbarkeit. Generative Modelle neigen zu
Halluzinationen oder unerwartetem Verhalten. Für geschäftskritische Prozesse ist ein «Black-Box»-Ansatz, bei dem ein
Agent autonom und intransparent entscheidet, nicht akzeptabel. Unternehmen benötigen die Gewissheit, dass automatisierte
Entscheidungen nachvollziehbar, prüfbar und erklärbar sind. Erst wenn die KI als verlässlicher Partner wahrgenommen
wird, der definierte Leitplanken respektiert, entsteht das notwendige Vertrauen für eine tiefe Integration in die
Kernprozesse.

### Konzeptioneller Ansatz

Der Lösungsansatz setzt auf deterministische Strukturen statt offener Entscheidungsschleifen. Anstatt Agenten
unkontrolliert agieren zu lassen, werden sie in definierte «Closed Workflows» eingebettet. Ein Agenten-Workflow
beschreibt exakt, welche Schritte ausgeführt werden dürfen und welche Datenquellen konsultiert werden müssen. Dies
garantiert, dass die KI nicht vom definierten Pfad abweicht. Dieses Prinzip wird durch eine umfassende Transparenz
ergänzt: Jede Aktion und jede herangezogene Quelle muss für den Benutzer und für Auditoren jederzeit sichtbar sein.

### Technische Umsetzung im Swiss AI Hub

In der Plattform werden diese Konzepte durch strikte Agenten-Baupläne und konfigurierbare Agenten-Profile umgesetzt.
Jeder Schritt eines Workflows ist als Event im System sichtbar und über das Phoenix-Tracing bis zum ursprünglichen
Dokumenten-Snippet rückverfolgbar. Die Plattform erzwingt Typensicherheit und validierte Ausgabenformate, um
sicherzustellen, dass nachgelagerte Systeme verlässliche Daten erhalten. Durch den integrierten `AgentTestRunner` im SDK
kann das Verhalten von Agenten vor dem Deployment systematisch geprüft werden, was die Qualitätssicherung im
KI-Lifecycle professionalisiert.
