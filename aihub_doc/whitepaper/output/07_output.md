# Datensicherheit und Datenfluss

In den vorangegangenen Kapiteln wurde dargelegt, wie Daten in die Plattform gelangen und dort verwaltet werden. Sobald
Unternehmensdaten jedoch den Sicherheitsperimeter eines KI-Systems betreten, verschieben sich die Anforderungen von
reiner Logistik hin zu kompromissloser Sicherheit. In einer Ära, in der Daten das wertvollste Asset darstellen, ist der
Schutz vor Diebstahl, Manipulation und unbefugtem Zugriff nicht verhandelbar. Der Übergang zum «Day 2», dem stabilen
Produktivbetrieb, erfordert eine Architektur, die nicht nur Daten speichert, sondern diese aktiv über ihren gesamten
Lebenszyklus hinweg verteidigt.

Dieses Kapitel beleuchtet die Sicherheitsarchitektur des Swiss AI Hub, die weit über traditionelle Firewalls hinausgeht.
Es beschreibt, wie die Plattform proaktiv gegen KI-spezifische Angriffsvektoren gehärtet wird, sensible Informationen
(PII) dynamisch schützt und den gesamten Datenfluss – von der technischen Eingabevalidierung bis zur unwiderruflichen
Löschung – absichert.

## Auf einen Blick

- **Defense-in-Depth:** Ein mehrschichtiges Sicherheitsmodell schützt Daten durch strikte Netzwerk-Isolation in fünf
  Zonen, Container-Härtung und validierte Eingabeprozesse.
- **Aktiver Schutz vor KI-Angriffen:** Spezialisierte «Input Guardrails» und technische Whitelists blockieren
  Prompt-Injection-Versuche und Schadcode-Uploads auf Protokoll- und Inhaltsebene.
- **Automatisierte PII-Anonymisierung:** Integrierte Erkennungsverfahren via Presidio identifizieren und maskieren
  Personenidentifizierbare Informationen (PII) dynamisch, bevor diese externe Sprachmodelle erreichen.
- **Verschlüsselung nach Industriestandard:** Durchgängige Verschlüsselung mittels TLS 1.2+ für Datenübertragungen
  (Data-in-Transit) und LUKS-basierte Volume-Verschlüsselung (Data-at-Rest) sichern die Vertraulichkeit.
- **Automatisierter Daten-Lebenszyklus:** Ephemere Daten werden nach festen Fristen von 30 Tagen automatisch gelöscht,
  um das «Recht auf Vergessenwerden» technisch und ohne manuellen Aufwand zu erzwingen.

## Schutz vor KI-spezifischen Bedrohungen und Systemhärtung

### Geschäftlicher Nutzen

Die Integration generativer KI eröffnet Unternehmen nicht nur neue Möglichkeiten, sondern exponiert sie auch gegenüber
neuartigen Bedrohungen. Angriffe wie «Prompt Injection», bei denen bösartige Akteure versuchen, die
Sicherheitsrichtlinien eines Modells durch manipulative Eingaben zu umgehen, oder das Einschleusen von Schadcode über
Datei-Uploads stellen reale Risiken dar. Ein erfolgreicher Angriff könnte zur Exfiltration vertraulicher Daten oder zur
Reputationsschädigung durch manipulierte Antworten führen. Sicherheitsverantwortliche benötigen daher eine
Verteidigungslinie, die spezifisch auf die Natur von LLM-Interaktionen zugeschnitten ist und Angriffe abwehrt, bevor sie
die Kernsysteme erreichen.

### Konzeptioneller Ansatz

Der Swiss AI Hub verfolgt eine «Defense-in-Depth»-Strategie. Sicherheit wird nicht als einzelne Schale um die Anwendung
gelegt, sondern in jeder Verarbeitungsphase durchgesetzt. Das Konzept unterscheidet zwischen klassischer
Eingabevalidierung, Container-Sicherheit und semantischen Schutzmechanismen (Guards). Während die Validierung
sicherstellt, dass Dateiformate und Protokolle den Spezifikationen entsprechen, analysieren semantische Wächter den
Inhalt der Kommunikation. Dies gilt sowohl für eingehende Daten (Input Guards) als auch für ausgehende Antworten der KI
(Output Guards), um zu verhindern, dass Modelle halluzinieren oder schädliche Inhalte generieren.

### Technische Umsetzung im Swiss AI Hub

Auf technischer Ebene implementiert die Plattform rigide Filtermechanismen für jeden Daten-In- und Egress. Bei
Datei-Uploads greift eine strikte Whitelist, die etwa 40 genehmigte Dateierweiterungen wie PDF, DOCX oder JSON zulässt.
Das System validiert dabei nicht nur die Endung, sondern prüft den tatsächlichen MIME-Typ des Inhalts, um «Extension
Spoofing» – das Tarnen einer ausführbaren Datei als harmloses Dokument – sowie Path-Traversal-Versuche und
Null-Byte-Injections zu unterbinden.

Für den Schutz der Interaktionsebene kommen spezialisierte Guardrails zum Einsatz. Eingangs-Schutzmechanismen
analysieren den Benutzer-Prompt, bevor er an das Agenten-Profil übergeben wird. Sie blockieren themenfremde Anfragen
mittels eines Agentenbeschreibungs-Schutzmechanismus. Auf Infrastrukturebene wird die Angriffsfläche durch gehärtete
Container minimiert. Dienste laufen standardmässig als nicht privilegierter Benutzer (UID 1000), was die Auswirkungen
potenzieller Container-Ausbrüche massiv reduziert. Die Erstellung der Container erfolgt über Multi-Stage-Builds, sodass
Build-Werkzeuge nicht im finalen Produktions-Image enthalten sind. Als Basis dienen minimale Slim-Images, die
regelmässig neu gebaut werden, um aktuelle Sicherheitspatches zu integrieren.

## Automatisierte Anonymisierung und PII-Schutz

### Geschäftlicher Nutzen

Der grösste Hemmschuh für die Nutzung von KI-Modellen in der Cloud ist der Datenschutz. Das unbedachte Senden von
Personenidentifizierbaren Informationen (PII) wie Namen, AHV-Nummern oder Kreditkartendaten an externe Anbieter stellt
oft einen Verstoss gegen interne Compliance-Vorgaben, das Schweizer Datenschutzgesetz (revDSG) oder die DSGVO dar.
Unternehmen stehen vor dem Dilemma, entweder auf leistungsfähige externe Modelle zu verzichten oder rechtliche Risiken
einzugehen. Der Swiss AI Hub löst diesen Konflikt durch eine intelligente Zwischenschicht, die als automatischer Filter
fungiert und sicherstellt, dass sensible Informationen den internen Sicherheitsperimeter niemals ungeschützt verlassen.

### Konzeptioneller Ansatz

Das Prinzip lautet «Sanitization at the Gateway». Bevor eine Anfrage das kontrollierte Netzwerk der Plattform verlässt,
muss sie bereinigt werden. Das System ist in der Lage, PII im laufenden Datenstrom zu erkennen und kontextabhängig zu
entscheiden, ob diese Informationen maskiert oder die gesamte Anfrage blockiert werden soll. Dieser Schutz erfolgt
zentral im LLM-Gateway, damit er für alle angeschlossenen Agenten-Profile gleichermassen wirksam ist, ohne dass für
jedes Projekt eigene Filterlogiken implementiert werden müssen. Ergänzend dazu schützen Ausgangs-Filter den Benutzer vor
der Anzeige sensibler Daten, die eventuell aus internen Wissensdatenbanken abgerufen wurden.

### Technische Umsetzung im Swiss AI Hub

Zentraler Baustein für diese Funktion ist die Integration von Presidio in das LLM-Gateway. Presidio analysiert jeden
Prompt mittels Mustererkennung und Named Entity Recognition (NER) auf PII in mehreren Sprachen, einschliesslich Deutsch,
Französisch und Italienisch. Das System bietet zwei primäre Betriebsmodi:

Im Maskierungsmodus werden erkannte Entitäten durch Platzhalter ersetzt, wodurch beispielsweise ein Name zu `[PERSON]`
wird. Das externe Modell erhält den Kontext, aber keine echten Daten. Im Blockierungsmodus wird die Anfrage bei
hochsensiblen Datenkategorien wie Kreditkartennummern komplett abgelehnt. Zusätzlich prüfen «Ausgangs-Schutzmechanismen»
auf Agenten-Ebene die generierten Antworten. Ein Schutzmechanismus für sensible Informationen redigiert PII, die aus
internen Dokumenten im RAG-Kontext stammen könnten, vor der Anzeige im Chatfenster zu `[REDACTED]`.

## Verschlüsselungsarchitektur und Netzwerk-Isolation

### Geschäftlicher Nutzen

Daten sind sowohl im Ruhezustand als auch während der Übertragung potenziellen Angriffen ausgesetzt. Ein physischer
Diebstahl von Festplatten oder das Abhören von Netzwerkverkehr im Firmennetzwerk darf nicht zur Kompromittierung von
Geschäftsgeheimnissen führen. Für Auditoren und Compliance-Abteilungen ist der Nachweis einer durchgängigen
Verschlüsselungskette und einer strikten Segmentierung der Netzwerke essenziell, um die Vertraulichkeit und Integrität
der verarbeiteten Informationen zu attestieren. Eine klare Trennung der Netzwerke begrenzt zudem den Schadensradius im
Falle einer Kompromittierung einzelner Komponenten.

### Konzeptioneller Ansatz

Die Sicherheitsarchitektur basiert auf Isolation und Kryptografie nach Industriestandards. Netzwerkseitig gilt das
Prinzip der minimalen Exposition: Nur zwingend notwendige Schnittstellen sind nach aussen sichtbar, während alle
internen Dienste in einem privaten Netzwerk kommunizieren. Die Plattform segmentiert den Verkehr in fünf isolierte Zonen
für Proxy, Backend, Daten, Storage und Egress. Kryptografisch setzt der Swiss AI Hub auf bewährte Protokolle wie TLS für
die Übertragung und Konzepte zur Vollverschlüsselung der Speichermedien, um den Zugriff auf physischer Ebene zu
verunmöglichen.

### Technische Umsetzung im Swiss AI Hub

Das Netzwerkdesign implementiert eine strikte Trennung mittels isolierter Docker-Netzwerke. Der Traefik Reverse Proxy
ist die einzige Komponente, die über die Ports 80 und 443 erreichbar ist. Er terminiert TLS-Verbindungen (erzwingt TLS
1.2+), verwaltet Zertifikate via Let's Encrypt und leitet den Verkehr an die internen Dienste weiter.
Backend-Komponenten wie Datenbanken oder das LLM-Gateway sind niemals direkt dem öffentlichen Internet ausgesetzt. Ein
spezielles Egress-Netzwerk ermöglicht ausgehende Verbindungen zu LLM-Providern, wobei die Inter-Container-Kommunikation
(ICC) deaktiviert ist, um seitliche Bewegungen von Angreifern zu verhindern.

Für die Datensicherheit gelten folgende kryptografische Massnahmen:

- **Data-in-Transit:** Die gesamte Kommunikation ist TLS-verschlüsselt. Sicherheits-Header wie HSTS und
  X-Content-Type-Options werden durch Traefik erzwungen. Auch WebSocket-Verbindungen nutzen das sichere WSS-Protokoll
  mit Origin-Validierung.
- **Data-at-Rest:** Persistente Daten werden auf Docker-Volumes gespeichert, die mittels LUKS (Linux Unified Key Setup)
  mit AES-256 verschlüsselt sind. Dies schützt Anwendungsdatenbanken, Vektordatenbank-Indizes und Dokumentenspeicher vor
  physischem Zugriff.

## Daten-Lebenszyklus und Revisionssichere Löschung

### Geschäftlicher Nutzen

Datenschutzgesetze fordern nicht nur den Schutz von Daten, sondern auch deren Begrenzung und rechtzeitige Löschung.
Unternehmen dürfen Daten nicht unbegrenzt horten, da dies rechtliche Altlasten erzeugt und die Speicherkosten erhöht.
Ein KI-System muss in der Lage sein, auf Anfragen von Betroffenen (Data Subject Access Requests) zu reagieren und das
«Recht auf Vergessenwerden» technisch umzusetzen. Ein automatisierter Daten-Lebenszyklus reduziert die
Compliance-Risiken und stellt sicher, dass nur Informationen aufbewahrt werden, die für den Betrieb oder gesetzliche
Nachweispflichten zwingend erforderlich sind.

### Konzeptioneller Ansatz

Der Swiss AI Hub unterscheidet konzeptionell zwischen ephemeren (flüchtigen) und permanenten Daten. Flüchtige Daten, die
für den unmittelbaren Betrieb oder das Caching notwendig sind, besitzen ein automatisches Verfallsdatum. Permanente
Daten wie Wissensdatenbanken oder Audit-Logs unterliegen definierten Aufbewahrungsrichtlinien. Dieser Ansatz stellt
sicher, dass das System sich selbst bereinigt. Zudem stehen Mechanismen bereit, um Daten auf explizite Anforderung
gezielt und nachweisbar zu löschen, ohne die Integrität der Audit-Trails für Sicherheitsanalysen zu gefährden.

### Technische Umsetzung im Swiss AI Hub

Die Plattform setzt diese Anforderungen durch technische Automatismen um. Hochgeschwindigkeits-Daten im Arbeitsspeicher
(Redis) wie Konversations-Caches unterliegen einer automatischen Ablauffrist (TTL) von 30 Tagen. Nach Ablauf dieses
Fensters werden die Daten ohne manuelles Zutun gelöscht. Workflow-Ereignisse werden via NATS JetStream verwaltet, wobei
doppelte Limits greifen: Daten werden entweder nach 30 Tagen oder beim Erreichen einer Kapazitätsgrenze von 10 Millionen
Nachrichten rotiert.

Die Plattform unterstützt Administratoren zudem bei der Erfüllung von Betroffenenrechten. Über APIs können
Benutzerprofile, spezifische Konversationsstränge oder Konto-Daten permanent entfernt werden. Während Inhalte gelöscht
werden, bleiben strukturelle Audit-Logs unveränderlich erhalten, um die Nachweisbarkeit von Aktionen gegenüber Revisoren
sicherzustellen.

## Sicherheits-Monitoring und Anomalieerkennung

### Geschäftlicher Nutzen

Sicherheit ist kein statischer Zustand, sondern ein kontinuierlicher Prozess. Um auf Vorfälle reagieren zu können,
benötigen IT-Teams Echtzeit-Transparenz. Es muss jederzeit beantwortet werden können, wer auf welche Ressourcen
zugegriffen hat und ob Unregelmässigkeiten im Datenverkehr vorliegen. Eine lückenlose Protokollierung von
Sicherheitsereignissen ist Voraussetzung für Zertifizierungen und ermöglicht eine schnelle Reaktion auf potenzielle
Bedrohungen. Durch proaktives Monitoring können Angriffsversuche wie Brute-Force oder exzessive Datenexporte erkannt
werden, bevor ein Schaden entsteht.

### Konzeptioneller Ansatz

Der Ansatz basiert auf vollständiger Observability mittels offener Standards. Sämtliche Authentifizierungs- und
Autorisierungsereignisse werden strukturiert erfasst. Das System nutzt OpenTelemetry, um Sicherheits-Logs mit Metadaten
anzureichern und zentral bereitzustellen. Dies ermöglicht die Korrelation von Ereignissen über verteilte
Systemkomponenten hinweg. Das Monitoring umfasst dabei nicht nur die technische Verfügbarkeit, sondern auch die
Sicherheitsebene, einschliesslich der Überwachung von API-Schlüssel-Nutzung und Budgetüberschreitungen im LLM-Gateway.

### Technische Umsetzung im Swiss AI Hub

Sämtliche sicherheitsrelevanten Aktionen werden protokolliert. Die Zugriffs-Logs erfassen jeden Login-Versuch und jede
Berechtigungsprüfung im Rahmen der rollenbasierten Zugriffskontrolle (RBAC). Jede Anfrage an die API wird mit
Benutzeridentität und der Autorisierungsentscheidung gespeichert. Sicherheitsteams können über Dashboards in SigNoz
Authentifizierungsmuster überwachen und auf Anomalien reagieren. Die Plattform unterstützt den Export dieser Logs an
externe SIEM-Systeme. Zusätzlich überwacht das LLM-Gateway die Kosten und Token-Nutzung in Echtzeit, wobei automatische
Budget-Sperren («Circuit Breakers») greifen, sobald vordefinierte Schwellenwerte erreicht werden, was einen wirksamen
Schutz vor finanziellem Missbrauch bietet.
