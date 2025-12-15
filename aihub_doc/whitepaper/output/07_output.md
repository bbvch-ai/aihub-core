# Datensicherheit und Datenfluss

In den vorangegangenen Kapiteln wurde dargelegt, wie Daten in die Plattform gelangen und verwaltet werden. Sobald
Unternehmensdaten jedoch den Sicherheitsperimeter eines KI-Systems betreten, verschieben sich die Anforderungen von
reiner Logistik hin zu kompromissloser Sicherheit. In einer Ära, in der Daten das wertvollste Asset darstellen, ist der
Schutz vor Diebstahl, Manipulation und unbefugtem Zugriff nicht verhandelbar.

Dieses Kapitel beleuchtet die Sicherheitsarchitektur des Swiss AI Hub, die weit über traditionelle Firewalls hinausgeht.
Es beschreibt, wie die Plattform proaktiv gegen KI-spezifische Angriffsvektoren härtet, sensible Informationen (PII)
dynamisch schützt und den gesamten Lebenszyklus der Daten – von der Entstehung bis zur unwiderruflichen Löschung –
absichert.

## Auf einen Blick

- **Defense-in-Depth:** Ein mehrschichtiges Sicherheitsmodell schützt Daten durch Netzwerk-Isolation, Container-Härtung
  (Non-Root) und strikte Eingabevalidierung auf Protokoll- und Inhaltsebene.
- **Aktiver Schutz vor KI-Angriffen:** Spezialisierte «Input Guardrails» und Whitelists blockieren
  Prompt-Injection-Versuche und Schadcode-Uploads, bevor sie verarbeitet werden.
- **Automatisierte PII-Anonymisierung:** Integrierte Erkennungsverfahren (Presidio) identifizieren und maskieren
  personenbezogene Daten dynamisch, um Datenschutzverstösse bei der Nutzung externer LLMs zu verhindern.
- **Verschlüsselung als Standard:** Durchgängige Verschlüsselung mittels TLS für Datenübertragung (Data-in-Transit) und
  Konzepte zur Volume-Verschlüsselung (Data-at-Rest) sichern die Vertraulichkeit.
- **Automatisierter Daten-Lebenszyklus:** Ephemere Daten werden nach festen Fristen (z.B. 30 Tage) automatisch gelöscht,
  um Speicher-Hygiene und «Recht auf Vergessenwerden» technisch zu erzwingen.

## Schutz vor KI-spezifischen Bedrohungen und Systemhärtung

### Geschäftlicher Nutzen

Die Integration generativer KI eröffnet Unternehmen nicht nur neue Möglichkeiten, sondern exponiert sie auch gegenüber
neuartigen Bedrohungen. Angriffe wie «Prompt Injection», bei denen bösartige Akteure versuchen, die
Sicherheitsrichtlinien eines Modells durch manipulative Eingaben zu umgehen, oder das Einschleusen von Schadcode über
Datei-Uploads stellen reale Risiken dar. Ein erfolgreicher Angriff könnte zur Exfiltration vertraulicher Daten oder zur
Reputationsschädigung durch manipulierte Antworten führen. Sicherheitsverantwortliche (CISOs) benötigen daher eine
Verteidigungslinie, die spezifisch auf die Natur von LLM-Interaktionen zugeschnitten ist und Angriffe abwehrt, bevor sie
die Kernsysteme erreichen.

### Konzeptioneller Ansatz

Der Swiss AI Hub verfolgt eine «Defense-in-Depth»-Strategie. Sicherheit wird nicht als einzelne Schale um die Anwendung
gelegt, sondern in jeder Verarbeitungsphase durchgesetzt. Das Konzept unterscheidet zwischen klassischer
Eingabevalidierung, Container-Sicherheit und semantischen Schutzmechanismen (Guardrails). Während die Validierung
sicherstellt, dass Dateiformate und Protokolle den Spezifikationen entsprechen, analysieren semantische Wächter den
Inhalt der Kommunikation. Dies gilt sowohl für eingehende Daten (Input Guards) als auch für ausgehende Antworten der KI
(Output Guards), um zu verhindern, dass Modelle halluzinieren oder schädliche Inhalte generieren. Zudem gilt für die
Ausführungsumgebung das Prinzip der minimalen Privilegien.

### Technische Umsetzung im Swiss AI Hub

Auf technischer Ebene implementiert die Plattform rigide Filtermechanismen. Bei Datei-Uploads greift eine strikte
Whitelist, die etwa 40 genehmigte Dateierweiterungen (z.B. PDF, DOCX, JSON, Bildformate) zulässt. Das System validiert
dabei nicht nur die Endung, sondern prüft den tatsächlichen MIME-Typ des Inhalts, um «Extension Spoofing» – das Tarnen
einer ausführbaren Datei als harmloses Dokument – sowie Path-Traversal-Versuche und Null-Byte-Injections zu unterbinden.
Dateien müssen zudem grösser als 0 Bytes sein, um leere Dateileichen zu vermeiden.

Für den Schutz der Interaktionsebene kommen spezialisierte Guardrails zum Einsatz. Eingangs-Schutzmechanismen
analysieren den Benutzer-Prompt, bevor er an einen Agenten übergeben wird. Sie blockieren themenfremde Anfragen mittels
eines «Agentenbeschreibungs-Schutzmechanismus» oder setzen benutzerdefinierte Richtlinien durch
«Few-Shot-Schutzmechanismen» durch.

Auf Infrastrukturebene wird die Angriffsfläche durch gehärtete Container minimiert. Dienste laufen standardmässig als
nicht privilegierter Benutzer (UID 1000), was die Auswirkungen potenzieller Container-Ausbrüche massiv reduziert. Die
Erstellung der Container erfolgt über Multi-Stage-Builds, sodass Build-Werkzeuge und Compiler nicht im finalen
Produktions-Image enthalten sind. Als Basis dienen minimale Slim-Images, die regelmässig neu gebaut werden, um aktuelle
Sicherheitspatches zu integrieren.

## Automatisierte Anonymisierung und PII-Schutz

### Geschäftlicher Nutzen

Der grösste Hemmschuh für die Cloud-Nutzung von KI in der Schweiz ist der Datenschutz. Das unbedachte Senden von
Personenidentifizierbaren Informationen (PII) – wie Namen, AHV-Nummern oder Kreditkartendaten – an externe
Modell-Anbieter wie OpenAI oder Google stellt oft einen Verstoss gegen interne Compliance-Vorgaben, das DSG oder die
DSGVO dar. Unternehmen stehen vor dem Dilemma, entweder auf leistungsfähige externe Modelle zu verzichten oder
rechtliche Risiken einzugehen. Der Swiss AI Hub löst diesen Konflikt durch eine intelligente Zwischenschicht, die als
automatischer Datenschutzbeauftragter fungiert.

### Konzeptioneller Ansatz

Das Prinzip lautet «Sanitization at the Gateway». Bevor eine Anfrage das kontrollierte Netzwerk der Plattform verlässt,
muss sie bereinigt werden. Sensible Daten dürfen die Hoheit des Unternehmens nicht ungeschützt verlassen. Das System
muss in der Lage sein, PII im laufenden Datenstrom zu erkennen und kontextabhängig zu entscheiden, ob diese
Informationen maskiert (ersetzt) oder die gesamte Anfrage blockiert werden soll. Dieser Schutz muss zentral erfolgen,
damit er für alle angeschlossenen Agenten und Anwendungen gleichermassen wirksam ist, ohne dass jeder Entwickler eigene
Filterlogiken implementieren muss.

### Technische Umsetzung im Swiss AI Hub

Zentraler Baustein für diese Funktion ist die Integration von **Presidio** in das LLM-Gateway (LiteLLM-Proxy). Presidio
analysiert jeden Prompt mittels Mustererkennung und Named Entity Recognition (NER) auf PII in mehreren Sprachen
(Deutsch, Englisch, Französisch, Italienisch).

Das System bietet zwei primäre Betriebsmodi, die administrativ konfiguriert werden können:

- **Maskierungsmodus:** Erkannte Entitäten werden durch Platzhalter ersetzt (z.B. wird «John Smith» zu `[PERSON]` oder
  eine E-Mail zu `[EMAIL_ADDRESS]`). Das externe Modell erhält den Kontext, aber keine echten Daten, und kann dennoch
  eine valide Antwort generieren.
- **Blockierungsmodus:** Bei hochsensiblen Datenkategorien wie Kreditkartennummern wird die Anfrage komplett abgelehnt
  und der Benutzer über den Sicherheitsverstoss informiert.

Ergänzend dazu prüfen «Ausgangs-Schutzmechanismen» (Output Guards) auf Agenten-Ebene die generierten Antworten. Ein
Schutzmechanismus für sensible Informationen kann PII, die eventuell aus internen Dokumenten abgerufen wurden (z.B. eine
Mitarbeiter-E-Mail in einem RAG-Kontext), vor der Anzeige im Chatfenster redigieren (`[REDACTED]`).

## Verschlüsselungsarchitektur und Netzwerk-Isolation

### Geschäftlicher Nutzen

Daten sind sowohl im Ruhezustand (Data-at-Rest) als auch während der Übertragung (Data-in-Transit) potenziellen
Angriffen ausgesetzt. Ein physischer Diebstahl von Festplatten aus einem Rechenzentrum oder das Abhören von
Netzwerkverkehr im Firmennetzwerk darf nicht zur Kompromittierung von Unternehmensgeheimnissen führen. Für Auditoren und
Compliance-Abteilungen ist der Nachweis einer durchgängigen Verschlüsselungskette und einer strikten Segmentierung der
Netzwerke essenziell, um die Vertraulichkeit und Integrität der verarbeiteten Informationen zu attestieren.

### Konzeptioneller Ansatz

Die Sicherheitsarchitektur basiert auf Isolation und Kryptografie nach Industriestandards. Netzwerkseitig gilt das
Prinzip der minimalen Exposition: Nur zwingend notwendige Schnittstellen sind nach aussen sichtbar, während alle
internen Dienste in einem privaten Netzwerk kommunizieren, das von aussen unerreichbar ist. Kryptografisch setzt die
Plattform auf bewährte Protokolle wie TLS für die Übertragung und Konzepte zur Vollverschlüsselung der Speichermedien.

### Technische Umsetzung im Swiss AI Hub

Das Netzwerkdesign implementiert eine strikte Trennung mittels isolierter Docker-Netzwerke. Nur der Reverse Proxy
(**Traefik**) ist über die Ports 80 und 443 erreichbar. Er terminiert die TLS-Verbindungen (erzwingt TLS 1.2+),
verwaltet Zertifikate automatisch via Let's Encrypt (in Produktionsumgebungen) und leitet den bereinigten Verkehr an die
internen Dienste weiter. Backend-Komponenten wie Datenbanken, der LiteLLM Proxy oder die KI-API sind niemals direkt dem
Internet ausgesetzt.

Für die Datensicherheit gelten folgende Massnahmen:

- **Data-in-Transit:** Die gesamte Kommunikation zwischen dem Client und der Plattform ist TLS-verschlüsselt.
  HTTP-Anfragen werden automatisch auf HTTPS umgeleitet. Sicherheits-Header wie HSTS und X-Content-Type-Options werden
  durch Traefik erzwungen. Auch die Verbindung zu externen Cloud-Diensten (z.B. Azure OpenAI) erfolgt ausschliesslich
  über HTTPS.
- **Data-at-Rest:** Das Sicherheitskonzept sieht vor, dass persistente Daten auf Docker-Volumes gespeichert werden, die
  mittels LUKS (Linux Unified Key Setup) mit AES-256 verschlüsselt sind. Dies schützt vor physischem Zugriff auf die
  Datenträger, wenn das System ausgeschaltet ist.
- **WebSocket-Sicherheit:** Echtzeit-Verbindungen nutzen das sichere WSS-Protokoll und validieren den Origin-Header, um
  Cross-Site-Hijacking zu verhindern.

## Daten-Lebenszyklus, Löschung und Compliance-Steuerung

### Geschäftlicher Nutzen

Datenschutzgesetze wie die DSGVO oder das Schweizer revDSG fordern nicht nur den Schutz von Daten, sondern auch deren
Begrenzung und Löschung. Unternehmen dürfen Daten nicht unbegrenzt horten. Ein KI-System, das Konversationen ewig
speichert, wird zur rechtlichen Altlast. Zudem müssen Organisationen in der Lage sein, auf Anfragen von Betroffenen
(Data Subject Access Requests, DSAR) zu reagieren und Auskunft über gespeicherte Daten zu geben. Ein automatisierter
Daten-Lebenszyklus reduziert Speicher-Kosten und minimiert das Compliance-Risiko.

### Konzeptioneller Ansatz

Der Swiss AI Hub unterscheidet konzeptionell zwischen ephemeren (flüchtigen) und permanenten Daten. Flüchtige Daten, die
für den unmittelbaren Betrieb oder das Caching notwendig sind, sollten ein automatisches Verfallsdatum haben. Permanente
Daten, wie Audit-Logs oder Wissensdatenbanken, unterliegen definierten Aufbewahrungsrichtlinien (Retention Policies).
Dieser Ansatz stellt sicher, dass das System sich selbst «reinigt» und Datenhalden vermieden werden. Zudem müssen
Mechanismen bereitstehen, um Daten auf explizite Anforderung gezielt und nachweisbar zu löschen.

### Technische Umsetzung im Swiss AI Hub

Die Plattform setzt diese Anforderungen durch technische Automatismen um:

- **Ephemere Daten:** Hochgeschwindigkeits-Daten im Arbeitsspeicher (Redis), wie Konversations-Caches oder
  Session-States, unterliegen einer automatischen Ablauffrist (TTL) von 30 Tagen. Nach Ablauf dieses Zeitfensters werden
  die Daten ohne manuelles Zutun gelöscht.
- **Workflow-Ereignisse:** Für die Nachvollziehbarkeit speichert das System Workflow-Events via NATS JetStream. Hier
  greifen doppelte Limits: Daten werden entweder nach 30 Tagen oder beim Erreichen einer Kapazitätsgrenze (z.B. 10
  Millionen Nachrichten) rotiert. Dies garantiert eine hohe Performance bei gleichzeitiger Begrenzung der Datenspur.
- **Recht auf Löschung & Auskunft:** Die Plattform unterstützt Administratoren bei der Erfüllung von Betroffenenrechten.
  Über APIs können Benutzerprofile, spezifische Konversationsstränge oder Konto-Daten permanent entfernt werden. Für
  Auskunftsbegehren (DSAR) lassen sich gespeicherte Benutzerdaten exportieren.
- **Auditierbarkeit:** Trotz Löschung von Inhalten bleiben strukturelle Audit-Logs (wer hat wann was getan)
  unveränderlich erhalten, um die Nachweisbarkeit von Aktionen gegenüber Revisoren sicherzustellen.

## Sicherheits-Monitoring und Auditierung

### Geschäftlicher Nutzen

Sicherheit ist kein statischer Zustand, sondern ein kontinuierlicher Prozess. Um auf Vorfälle reagieren zu können,
benötigen IT-Teams Echtzeit-Transparenz. Es muss jederzeit beantwortet werden können: «Wer greift worauf zu?» und «Gibt
es Anomalien im Datenverkehr?». Eine lückenlose Protokollierung von Sicherheitsereignissen ist nicht nur Best Practice,
sondern oft Voraussetzung für Zertifizierungen.

### Konzeptioneller Ansatz

Der Ansatz basiert auf vollständiger Observability mittels offener Standards. Authentifizierungs- und
Autorisierungsereignisse werden strukturiert erfasst. Das System nutzt OpenTelemetry, um Sicherheits-Logs mit Metadaten
anzureichern und zentralisiert bereitzustellen. Dies ermöglicht die Korrelation von Ereignissen über verteilte
Systemkomponenten hinweg.

### Technische Umsetzung im Swiss AI Hub

Sämtliche sicherheitsrelevanten Aktionen werden protokolliert:

- **Zugriffs-Logs:** Jeder Login-Versuch, jede Token-Validierung und jede Berechtigungsprüfung (RBAC) wird erfasst.
- **API-Audit:** Jede Anfrage an die API wird mit Benutzeridentität, angeforderter Ressource und
  Autorisierungsentscheidung (Allow/Deny) gespeichert.
- **Echtzeit-Überwachung:** Sicherheitsteams können über Dashboards (z.B. in SigNoz) Authentifizierungsmuster überwachen
  und auf Anomalien wie Brute-Force-Attacken oder ungewöhnliche Zugriffsmuster reagieren. Die Plattform unterstützt den
  Export dieser Logs an externe SIEM-Systeme zur weiteren Analyse.
