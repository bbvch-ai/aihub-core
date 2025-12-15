# Die Business-Herausforderung – AI im Unternehmen

Der aktuelle Hype um generative KI verdeckt oft eine unbequeme Wahrheit: Es ist trivial, an einem Nachmittag eine
beeindruckende Demo zu erstellen, aber ausserordentlich schwierig, ein produktives, unternehmenstaugliches System zu
bauen. Viele Organisationen befinden sich aktuell in einer Phase der Desillusionierung. Nach erfolgreichen ersten Tests
mit Tools wie LangChain oder direkten API-Aufrufen an OpenAI stellen sie fest, dass der Weg zur Produktivsetzung durch
massive infrastrukturelle Hürden blockiert ist.

Dieses Kapitel analysiert die Diskrepanz zwischen Prototyping und Engineering und beleuchtet die spezifischen
Herausforderungen für Schweizer Unternehmen. Es zeigt auf, warum der Versuch, KI-Infrastruktur selbst zu bauen, oft in
einer teuren Sackgasse endet und wie die Lücke zwischen dem ersten «Wow»-Effekt und einem stabilen Betrieb («Day 2»)
geschlossen werden kann.

## Auf einen Blick

- **Infrastruktur-Lücke:** Der Schritt vom Prototyp zur Produktion scheitert oft an fehlenden Enterprise-Funktionen wie
  Authentifizierung, Monitoring und Rollenmanagement.
- **Kosten-Transparenz:** Ohne zentrale Steuerung führen fragmentierte Einzellösungen zu unkontrollierbaren Kosten und
  undurchsichtigen «Total Cost of Ownership».
- **Schatten-IT:** Isolierte KI-Experimente in Fachabteilungen erzeugen Datensilos und Sicherheitsrisiken, die zentral
  kaum noch zu managen sind.
- **Schweizer Compliance:** Strenge Anforderungen an die Datensouveränität blockieren oft die Nutzung gängiger
  US-Cloud-Dienste, was zu einem Innovationsstau führt.
- **Vorhersehbarkeit:** Für geschäftskritische Prozesse sind deterministische Abläufe («Closed Workflows») notwendig, um
  das «Black-Box»-Risiko autonomer Agenten zu eliminieren.

## Die Infrastrukturlücke: Von der Demo zur Realität

### Geschäftlicher Nutzen

Ein funktionierender Prototyp beantwortet selten die Fragen, die für den operativen Betrieb entscheidend sind: Wie
skalieren wir die Lösung? Wer hat Zugriff auf welche Daten? Was passiert bei Fehlern? Für Entscheidungsträger bedeutet
diese Lücke ein hohes Risiko. Projekte bleiben oft im Pilotstadium stecken («Pilot Purgatory»), weil die notwendige
Infrastruktur für Sicherheit und Governance fehlt. Dies führt zu Fehlinvestitionen, da die Time-to-Value durch den
nachträglichen Aufbau von Basistechnologie massiv verzögert wird. IT-Teams binden wertvolle Ressourcen in der
Entwicklung von Fundamenten, anstatt geschäftlichen Mehrwert zu generieren.

### Konzeptioneller Ansatz

Das Kernproblem liegt in der Unterscheidung zwischen KI-Logik und Infrastruktur. Bibliotheken unterstützen Entwickler
beim Bau der Agenten, ignorieren aber betriebliche Realitäten. Eine Enterprise-Lösung benötigt einen «Infrastructure as
Product»-Ansatz. Komponenten wie Authentifizierung, Daten-Pipelines und Audit-Trails dürfen nicht für jedes Projekt neu
erfunden werden, sondern müssen als stabile Plattform bereitstehen. Nur so lässt sich der Sprung vom «Day 1»
(Entwicklung) zum «Day 2» (Betrieb) wirtschaftlich vollziehen.

### Technische Umsetzung im Swiss AI Hub

Der Swiss AI Hub schliesst diese Lücke, indem er die für den Betrieb notwendigen Komponenten integral mitliefert.
Anstatt eigene Lösungen für die Benutzerverwaltung zu bauen, erben alle Dienste automatisch die Anbindung an den
Identity Provider via SSO/OAuth. Für die operative Sicherheit sorgt eine integrierte Beobachtbarkeit auf vier Ebenen:
Infrastruktur-Monitoring via OpenTelemetry, Agenten-Tracing via Phoenix, sowie detaillierte Einsichten in
Workflow-Events und Daten-Pipelines. Damit wird aus einem losen Verbund von Skripten eine verwaltbare
Enterprise-Architektur.

## Fragmentierung, Schatten-IT und Kostenkontrolle

### Geschäftlicher Nutzen

Ohne eine zentrale Plattform tendieren Abteilungen dazu, isolierte Lösungen zu implementieren. Das Marketing nutzt
ChatGPT-Abos, die IT experimentiert mit Azure OpenAI und die Entwicklung baut lokale RAG-Systeme. Diese Fragmentierung
führt zu intransparenten Kostenstrukturen und fördert Schatten-IT. Für den CFO wird es unmöglich, die effektiven Kosten
zu ermitteln oder Budgets zuzuweisen. Zudem entstehen Datensilos, in denen Wissen gefangen bleibt. Das Risiko von
Compliance-Verstössen steigt mit jeder unkontrollierten Einzellösung.

### Konzeptioneller Ansatz

Die Lösung liegt in der Konsolidierung auf einer mandantenfähigen Plattform, die als zentrales Gateway fungiert. Anstatt
direkter API-Zugriffe auf Modell-Provider durch einzelne Mitarbeiter, läuft jeglicher Verkehr über eine kontrollierte
Instanz. Dies ermöglicht eine zentrale Durchsetzung von Richtlinien, Quotas und Budgets. Gleichzeitig wird verhindert,
dass technologische Sackgassen entstehen, da die zugrundeliegenden Modelle ausgetauscht werden können, ohne die
darüberliegenden Geschäftsprozesse zu beeinträchtigen.

### Technische Umsetzung im Swiss AI Hub

Technisch realisiert der Swiss AI Hub diese Zentralisierung durch das LLM-Gateway (basierend auf LiteLLM). Diese
Komponente abstrahiert die verschiedenen Modell-Provider und ermöglicht ein granulares Kostenmanagement. Administratoren
können Budgets auf Benutzer- oder Team-Ebene definieren und Ausgaben in Echtzeit überwachen. Die Plattform verhindert
Silos zudem durch zentralisierte Wissensdatenbanken, die über standardisierte Daten-zu-Wissen-Pipelines (unter Nutzung
von Docling und Milvus) befüllt werden, sodass aufbereitetes Wissen organisationsweit sicher wiederverwendet werden
kann.

## Die Schweizer Compliance-Hürde und Datensouveränität

### Geschäftlicher Nutzen

Spezifisch für den Schweizer Markt ist die strenge Auslegung von Datenschutz und Datensouveränität. Organisationen im
öffentlichen Sektor oder in regulierten Branchen dürfen sensible Unternehmensdaten (PII) oft nicht an Cloud-Dienste im
Ausland übermitteln. Dies führt zu einer Blockadehaltung: Innovation wird untersagt, weil gängige SaaS-Lösungen die
Anforderungen an die Datenresidenz nicht erfüllen. Unternehmen stehen vor dem Dilemma, entweder auf KI zu verzichten
oder sich in einer rechtlichen Grauzone zu bewegen.

### Konzeptioneller Ansatz

Um dieses Dilemma aufzulösen, muss die Architektur eine flexible Datenhaltung ermöglichen, die sich strikt nach der
Klassifizierung der Daten richtet. Datensouveränität bedeutet hier, dass der Kunde die physische Kontrolle über
Speicherort und Verarbeitung behält. Es muss möglich sein, hochsensible Daten ausschliesslich On-Premise mit lokalen
Modellen zu verarbeiten, während weniger kritische Daten optional über Schweizer Cloud-Infrastrukturen laufen können.
Entscheidend ist, dass Daten den definierten Sicherheitsperimeter niemals ungewollt verlassen.

### Technische Umsetzung im Swiss AI Hub

Der Swiss AI Hub adressiert dies durch seine containerbasierte Architektur, die vollständig in der Infrastruktur des
Mandanten betrieben wird. Sensible Unternehmensdaten werden lokal in der Vektordatenbank gespeichert. Für zusätzliche
Sicherheit sorgt die Integration von Presidio zur automatischen Erkennung und Maskierung von PII, noch bevor ein Prompt
an ein Modell gesendet wird. Zudem unterstützt die Plattform den Einsatz von Open-Source-Modellen (wie Mistral oder
DeepSeek), sodass eine vollständige «Air-Gapped»-Installation ohne Internetverbindung realisierbar ist.

## Vertrauen durch Prozess-Stabilität

### Geschäftlicher Nutzen

Ein weiteres Hindernis für den produktiven KI-Einsatz ist die mangelnde Vorhersehbarkeit. Generative Modelle neigen zu
Halluzinationen oder unerwartetem Verhalten. Für geschäftskritische Prozesse ist ein «Black-Box»-Ansatz, bei dem ein
Agent autonom und intransparent entscheidet, nicht akzeptabel. Unternehmen benötigen die Gewissheit, dass automatisierte
Entscheidungen nachvollziehbar, prüfbar und erklärbar sind. Ohne dieses Vertrauen bleibt KI eine Spielerei, die nicht in
Kernprozesse integriert wird.

### Konzeptioneller Ansatz

Der Lösungsansatz setzt auf deterministische Strukturen statt offener Entscheidungsschleifen. Anstatt Agenten freie Hand
zu lassen, werden sie in definierte «Closed Workflows» eingebettet. Ein Agenten-Workflow beschreibt exakt, welche
Schritte ausgeführt werden dürfen und welche Datenquellen konsultiert werden müssen. Dies garantiert, dass die KI nicht
vom definierten Pfad abweicht. Ergänzt wird dies durch das Prinzip «Human-in-the-Loop», bei dem kritische Schritte eine
explizite menschliche Freigabe erfordern.

### Technische Umsetzung im Swiss AI Hub

In der Plattform werden diese Konzepte durch strikte Agenten-Baupläne und konfigurierbare Agenten-Profile umgesetzt.
Jeder Schritt eines Workflows ist als Event im System sichtbar und debugbar. Die Plattform erzwingt Typensicherheit und
validierte Ausgabenformate, um sicherzustellen, dass nachgelagerte Systeme verlässliche Daten erhalten. Durch den
integrierten `AgentTestRunner` im SDK kann das Verhalten von Agenten vor dem Deployment deterministisch geprüft werden,
um sicherzustellen, dass Änderungen keine Regressionen in der Entscheidungsqualität verursachen.
