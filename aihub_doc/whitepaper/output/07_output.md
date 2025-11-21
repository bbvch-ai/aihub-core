# Kapitel 07: Datensicherheit und Datenfluss

Die effektive und vertrauenswürdige Nutzung von Künstlicher Intelligenz in Schweizer Unternehmen erfordert einen
durchgängigen Schutz sensibler Daten über ihren gesamten Lebenszyklus hinweg. Von der ersten Interaktion über die
interne Verarbeitung bis zur Ausgabe muss die Integrität, Vertraulichkeit und Verfügbarkeit von Informationen jederzeit
gewährleistet sein. Dieses Kapitel legt dar, wie der Swiss AI Hub eine robuste Sicherheitsarchitektur implementiert, um
manipulative Eingaben abzuwehren, unbeabsichtigten Datenabfluss zu verhindern und ein Höchstmass an Datensicherheit für
Unternehmen zu realisieren.

## 1. Schutz vor intelligenten Bedrohungen: KI-spezifische Eingabe- und Ausgabe-Wächter

Die Einführung von KI-Systemen birgt neue, spezifische Sicherheitsrisiken, wie etwa Prompt-Injection oder
Jailbreaking-Versuche, die darauf abzielen, Sprachmodelle zu manipulieren oder zu umgehen. Ohne spezialisierte
Schutzmechanismen können solche Angriffe die Vertrauenswürdigkeit der KI-Antworten untergraben und zu unerwünschtem oder
schädlichem Verhalten führen.

### Mehrwert und Nutzen: Verlässlichkeit und Manipulationsschutz

Für C-Level-Führungskräfte bedeutet dies die Gewissheit, dass die KI-Systeme des Unternehmens gegen neuartige
Angriffsvektoren abgesichert sind und stets im Einklang mit Unternehmensrichtlinien agieren. Dies fördert die Akzeptanz
von KI-Anwendungen und minimiert operationelle und Compliance-Risiken. IT-Sicherheitsteams erhalten spezialisierte
Werkzeuge, um die Integrität und den Schutz der KI-Interaktionen in Echtzeit zu gewährleisten, wodurch sie sich auf die
Wertschöpfung durch KI konzentrieren können, anstatt grundlegende Sicherheitslücken zu adressieren.

### Konzepte & Prozesse: Agenten-Wächter und zweistufige Prüfung

Der Swiss AI Hub begegnet diesen Herausforderungen mit einem System von sogenannten LLM-Wächtern ("Guardrails"), die
KI-Agenten-Interaktionen in Echtzeit überwachen. Diese Wächter operieren präventiv an zwei kritischen Punkten im
Datenfluss: bei der Eingabe (Input) und bei der Ausgabe (Output). Input-Wächter analysieren Benutzerfragen, bevor der
Agent diese verarbeitet, und filtern themenfremde Anfragen oder Richtlinienverstösse heraus. Output-Wächter prüfen die
generierten Agentenantworten, bevor sie an den Benutzer ausgeliefert werden, um deren Qualität, Angemessenheit und
Sicherheit zu verifizieren.

### Technische Umsetzung im Swiss AI Hub: Konfigurierbare LLM-Wächter

Die technische Implementierung der LLM-Wächter im Swiss AI Hub umfasst verschiedene spezialisierte Komponenten:

- **Input-Wächter** wie der `Agentenbeschreibungs-Wächter` stellen sicher, dass Fragen zur definierten Funktion des
  Agenten passen und blockieren irrelevante Anfragen. Der `Few-Shot-Wächter` erzwingt benutzerdefinierte Richtlinien,
  indem er Muster anhand von konfigurierbaren Beispielen lernt und ähnliche Anfragen blockiert oder zulässt.
- **Output-Wächter** umfassen den `Kontext-Hinreichend-Wächter`, der prüft, ob der Agent über genügend Informationen aus
  den Wissensdatenbanken verfügt, um präzise zu antworten, was "Halluzinationen" (erfundene Antworten) entgegenwirkt.
  Ein `Wächter für sensible Informationen` erkennt und redigiert vertrauliche oder personenbezogene Daten (PII) aus den
  Antworten, bevor diese an Benutzer ausgeliefert werden, und ersetzt sie beispielsweise durch `[REDACTED]`. Diese
  Wächter können je nach Agentendesign und Risikostufe konfiguriert oder als obligatorisch implementiert werden.

## 2. Umfassende Datenanonymisierung und PII-Schutz

Die Verarbeitung personenbezogener Daten (PII) durch externe Sprachmodelle oder in ungeschützten Umgebungen stellt ein
erhebliches Compliance- und Datenschutzrisiko dar. Insbesondere für Schweizer Unternehmen mit strengen
Datenschutzauflagen ist es entscheidend, sensible Informationen im Datenfluss präventiv zu schützen.

### Mehrwert und Nutzen: Regulatorische Sicherheit und Vertrauensbildung

Diese Funktion schafft die notwendige Grundlage, um KI-Anwendungen auch in datensensiblen Bereichen rechtskonform
(revDSG, DSGVO) und vertrauenswürdig einzusetzen. C-Level-Verantwortliche können sicher sein, dass personenbezogene
Daten im Umgang mit KI-Systemen geschützt sind. IT-Teams profitieren von einer automatisierten Lösung, die das manuelle
Redigieren von Daten überflüssig macht, den administrativen Aufwand reduziert und das Risiko menschlicher Fehler
eliminiert, wodurch der Datenschutz von Beginn an gewährleistet ist.

### Konzepte & Prozesse: Vorverarbeitung vor LLM-Aufruf

Der Swiss AI Hub verfolgt einen "Privacy by Design"-Ansatz, bei dem personenbezogene Daten identifiziert und
anonymisiert werden, bevor sie in Kontakt mit potenziell exponierenden Systemen wie externen grossen Sprachmodellen
(LLMs) kommen. Dies stellt sicher, dass selbst bei einem theoretischen Kompromittierung eines externen LLM-Anbieters
keine identifizierbaren PII-Daten offengelegt werden.

### Technische Umsetzung im Swiss AI Hub: Presidio-Integration

Die Plattform integriert `Presidio`, eine spezialisierte Bibliothek für die Erkennung und Anonymisierung sensibler
Daten. Presidio identifiziert vordefinierte oder benutzerdefinierte Entitätstypen (z.B. Namen, Adressen,
E-Mail-Adressen, Sozialversicherungsnummern) in Texten. Diese PII-Informationen werden dynamisch im Datenstrom
anonymisiert oder geschwärzt. Konkret bedeutet dies, dass alle LLM-Anfragen, die potenzielle PII enthalten könnten,
diesen Anonymisierungsprozess durchlaufen, bevor sie das interne System verlassen und beispielsweise an einen
LLM-Provider übermittelt werden. Dies ist eine entscheidende präventive Massnahme gegen den ungewollten Abfluss
sensibler Informationen.

## 3. Durchgängige Verschlüsselung: Data-at-Rest und Data-in-Transit

Die Vertraulichkeit und Integrität von Daten ist nur gewährleistet, wenn sie über ihren gesamten Lebenszyklus – sowohl
im Ruhezustand (Data-at-Rest) als auch während der Übertragung (Data-in-Transit) – durch moderne kryptografische
Verfahren geschützt sind. Dies ist eine grundlegende Anforderung für jede Unternehmens-IT und insbesondere für den
Umgang mit sensiblen Informationen in KI-Systemen.

### Mehrwert und Nutzen: Maximale Vertraulichkeit und Compliance-Sicherheit

Für Unternehmen bedeutet die durchgängige Verschlüsselung einen umfassenden Schutz vor unbefugtem Zugriff,
Datendiebstahl und Manipulation, selbst im Falle eines physischen Zugriffs auf die Infrastruktur oder des Abhörens von
Kommunikationskanälen. Dies ist essenziell für die Einhaltung regulatorischer Anforderungen (revDSG, DSGVO) und zur
Sicherung des Unternehmensrufs. IT-Experten erhalten eine Sicherheitsarchitektur, die auf etablierten Standards basiert
und somit eine hohe Auditierbarkeit und langfristige Absicherung der Daten gewährleistet.

### Konzepte & Prozesse: Zwei-Säulen-Verschlüsselung

Die Plattform implementiert ein zweistufiges Verschlüsselungskonzept: Erstens werden alle persistent gespeicherten Daten
vor unbefugtem Zugriff geschützt. Zweitens wird die gesamte Datenkommunikation, sowohl nach aussen als auch (teilweise)
innerhalb der Plattform, kryptografisch gesichert. Schlüsselmanagement und zertifikatbasierte Authentifizierung ergänzen
diese Strategie.

### Technische Umsetzung im Swiss AI Hub: LUKS, TLS und Zertifikatsmanagement

Der Swiss AI Hub integriert umfassende Verschlüsselungsmechanismen:

- **Verschlüsselung im Ruhezustand (Data-at-Rest):** Das geplante Sicherheitskonzept sieht eine
  `LUKS-Volume-Verschlüsselung` für alle persistenten Docker-Volumes vor. Dies umfasst Anwendungsdatenbanken,
  Vektordatenbank-Indizes, Dokumentenspeicherung, Konfigurationsdaten, Geheimnisse und Protokolle. LUKS bietet eine
  AES-256-Verschlüsselung im XTS-Modus und schützt Daten auch bei physischem Zugriff oder Diebstahl der Speichermedien.
  Geheimnisse und sensitive Konfigurationsdaten werden über Umgebungsvariablen, Azure Key Vault oder Docker-Secrets
  verwaltet.
- **Verschlüsselung während der Übertragung (Data-in-Transit):** Die gesamte Kommunikation zwischen der Plattform und
  externen Clients sowie externen Diensten wird mittels `Transport Layer Security (TLS)` Protokollen verschlüsselt.
  - **Edge-Verschlüsselung:** `Traefik` dient als Reverse-Proxy und Ingress-Controller und übernimmt die
    TLS-Terminierung am Netzwerkrand. Es unterstützt `TLS 1.2 und TLS 1.3` und leitet automatisch von HTTP zu HTTPS
    weiter. Durch die `Let's Encrypt-Integration` werden Zertifikate automatisiert bereitgestellt und erneuert.
    Sicherheits-Header wie `Strict-Transport-Security (HSTS)` werden zur weiteren Härtung angewendet, was auch Perfect
    Forward Secrecy (PFS) über moderne TLS-Suiten gewährleistet.
  - **Externe Diensteverbindungen:** Alle Verbindungen von der Plattform zu externen Diensten (z.B. Azure OpenAI, Google
    Gemini, OAuth/OIDC-Anbieter) nutzen HTTPS mit strikter `Zertifikatsvalidierung`, um Man-in-the-Middle-Angriffe zu
    verhindern. Die `LiteLLM-Proxy-Schicht` sichert hierbei die Kommunikation zu den LLM-Anbietern.
  - **Interne Kommunikation:** Die Kommunikation zwischen Docker-Containern im internen Docker-Netzwerk ist durch
    `Netzwerkisolation` geschützt. Dieser Datenverkehr ist jedoch auf der Anwendungsebene **nicht** standardmässig
    verschlüsselt. Für Multi-Host-Deployments, die verschlüsselte Inter-Service-Kommunikation erfordern, könnten
    zusätzliche Massnahmen wie Service Mesh oder IPsec implementiert werden.
  - **WebSocket-Verbindungen:** Echtzeit-Event-Streaming über WebSocket-Verbindungen wird durch `WSS (WebSocket Secure)`
    und `Origin-Validierung` geschützt.

## 4. Logische Isolation und Mandantentrennung

In komplexen Unternehmensumgebungen, insbesondere bei der Nutzung durch verschiedene Abteilungen oder in
Multi-Tenant-Szenarien, ist die strikte Trennung von Datenräumen von entscheidender Bedeutung. Das Verhindern von
unautorisierten Datenzugriffen und Überschneidungen ist eine zentrale Anforderung für Datensouveränität und Compliance.

### Mehrwert und Nutzen: Strikte Datenhoheit und Compliance-Erfüllung

Die strikte Mandantentrennung gewährleistet, dass jede Organisation oder Abteilung die vollständige Kontrolle über ihre
Daten behält und kein unautorisierter Informationsaustausch stattfindet. Dies ist unerlässlich für die Einhaltung des
Schweizer Datenschutzgesetzes (revDSG) und der DSGVO, die hohe Anforderungen an die Datenisolation stellen. Für
C-Level-Führungskräfte bedeutet dies die Minimierung des Risikos von Datenlecks und die Sicherstellung der Datenhoheit,
auch bei der Nutzung gemeinsam genutzter Infrastruktur-Ressourcen.

### Konzepte & Prozesse: Dedizierte Instanzen und zustandslose Backends

Der Swiss AI Hub ist primär für `Single-Tenant-Bereitstellungen` konzipiert, die eine vollständige Isolation
gewährleisten. Bei `Multi-Tenant-Bereitstellungen` wird eine logische Trennung durch dedizierte Infrastruktur pro Tenant
und zustandslose, gemeinsam genutzte Backend-Ressourcen erreicht, die keine sensiblen Daten speichern.

### Technische Umsetzung im Swiss AI Hub: Isolierte Stacks und Proxy-Layer

- **Single-Tenant-Bereitstellung:** Jede Organisation erhält eine `vollständige, eigenständige AI-Hub-Instanz` mit
  dedizierten Datenbanken (FerretDB/PostgreSQL), Vektor-Stores (Milvus oder Azure AI Search), Dateispeichern (SeaweedFS
  oder Azure Data Lake) und allen Anwendungsdiensten. Dies gewährleistet eine `vollständige Datenisolation`, bei der
  Daten nicht zwischen Organisationen übertragen werden können. Die physische Isolation kann durch
  `On-Premise`-Bereitstellung auf eigenen Servern oder in einer `Private Cloud` des Kunden (z.B. in einem Schweizer
  Rechenzentrum) erreicht werden.
- **Multi-Tenant-Bereitstellung:** Mehrere Tenant-Instanzen können `zustandslose LLM-Backend-Ressourcen` (wie Azure
  OpenAI, Google Gemini oder selbst gehostete Modelle) gemeinsam nutzen. Hierbei hat jedoch jeder Tenant einen
  `eigenen LiteLLM-Proxy`, der die LLM-Anfragen verwaltet. Dieser Proxy speichert keine Prompts oder Antworten, sodass
  konversationeller Kontext und Benutzerdaten stets innerhalb der jeweiligen Tenant-Instanz verbleiben. Es gibt keine
  direkte Kommunikation zwischen den Tenant-Instanzen selbst, und die Datenisolation wird durch separate Datenbanken und
  Vektor-Stores pro Tenant aufrechterhalten.

## 5. Sichere Datenaufnahme und externe Integrationen

Die Sicherheit eines KI-Systems beginnt mit der Integrität der aufgenommenen Daten. Das Einschleusen bösartiger Dateien
oder unautorisierte Zugriffe über externe Integrationen kann die gesamte Wissensbasis kompromittieren und zu
unzuverlässigen KI-Antworten führen.

### Mehrwert und Nutzen: Robuste Datenintegrität und sichere Schnittstellen

Diese Sicherheitsmassnahmen gewährleisten, dass die Wissensbasis des Swiss AI Hub vor externen Bedrohungen und
Manipulationen geschützt ist. C-Level-Führungskräfte können sich auf die Verlässlichkeit der KI-generierten
Informationen verlassen. IT-Sicherheitsteams profitieren von robusten Validierungs- und Schutzmechanismen an allen Ein-
und Austrittspunkten, die die Angriffsfläche reduzieren und die Sicherheit der gesamten Datenlandschaft erhöhen, wodurch
die Compliance mit Unternehmensrichtlinien und externen Standards sichergestellt wird.

### Konzepte & Prozesse: Strikte Eingabevalidierung und gehärtete Schnittstellen

Die Plattform setzt auf eine mehrstufige Eingabevalidierung für alle hochgeladenen Dokumente sowie auf gehärtete und
authentifizierte Schnittstellen für die Integration mit externen Datenquellen. Zusätzlich werden Mechanismen zum Schutz
vor Überlastung und Missbrauch der API eingesetzt.

### Technische Umsetzung im Swiss AI Hub: Whitelisting, Rate-Limiting und sichere Konnektoren

- **Umfassende Eingabevalidierung für Uploads:** Die Plattform implementiert eine strikte `Whitelist für Dateitypen`,
  die Uploads auf etwa 40 genehmigte Erweiterungen (Dokumente, Bilder, Audio, strukturierte Daten) beschränkt. Eine
  `Validierung des MIME-Typs` verhindert das Verschleiern bösartiger Dateien. `Validierung von Dateinamen` blockiert
  Path Traversal-Versuche (z.B. `..`, `/`, `\`), Erweiterungs-Spoofing und Null-Bytes. Zudem werden
  Dateigrössenbeschränkungen erzwungen, um Ressourcenerschöpfung und das Hochladen potenziell schädlicher Grossdateien
  zu verhindern.
- `UNKLARHEIT IN DER DOKU - BITTE PRÜFEN: Die Quelldokumentation beschreibt keine explizite Funktion für einen Malware-Scan während der Dokumentenaufnahme, obwohl dies in den Kernaussagen des Kapitels erwähnt wird. Es wird angenommen, dass dies eine ergänzende, organisatorische oder zukünftige technische Implementierung wäre.`
- **Sichere Anbindung externer Datenquellen:** Agenten und Pipelines können über HTTPS (Port 443) mit bestehenden
  Unternehmenssystemen wie SharePoint, Confluence oder kundenspezifischen REST/SOAP-APIs verbunden werden. Dabei werden
  branchenübliche `Authentifizierungsmethoden` wie OAuth2 (z.B. über Azure AD App), API-Tokens oder Mutual TLS (mTLS)
  für Service-to-Service-Kommunikation unterstützt, um einen sicheren Zugriff zu gewährleisten.
- **Schutz vor API-Missbrauch und DoS:** Der `Traefik Reverse Proxy` als einziger Entry Point implementiert
  `Rate Limiting`-Funktionen, um Backend-Dienste vor Brute-Force- und einfachen Denial-of-Service (DoS)-Angriffen zu
  schützen. Der `LiteLLM-Proxy` erzwingt zudem `pro-Tenant-Anfragebegrenzungen` und Budgets, um Missbrauch zu verhindern
  und die Kosten zu kontrollieren.

## 6. Revisionssichere Datenlöschung und -aufbewahrung

Das "Recht auf Vergessenwerden" (Right to be Forgotten) und die Anforderungen an definierte
Datenaufbewahrungsrichtlinien sind zentrale Aspekte des Datenschutzes. Eine Plattform, die sensible Unternehmensdaten
verarbeitet, muss in der Lage sein, Informationen sicher und nachweisbar zu löschen und deren Verbleib über den gesamten
Lebenszyklus transparent zu machen.

### Mehrwert und Nutzen: Konformität und Nachweisbarkeit

Diese Funktionen stellen sicher, dass Unternehmen die gesetzlichen Anforderungen (revDSG, DSGVO) an die Datenlöschung
und -aufbewahrung erfüllen können, was die Compliance-Risiken minimiert. C-Level-Verantwortliche stärken das Vertrauen
in die Datenhandhabung der KI-Systeme und können Auskunfts- und Löschrechte effektiv unterstützen. IT- und
Compliance-Teams erhalten die notwendigen Werkzeuge, um Daten-Life-Cycles zu verwalten und revisionssichere Nachweise
über Löschvorgänge zu erbringen.

### Konzepte & Prozesse: Gestaffelte Aufbewahrung und Unterstützung des Löschrechts

Der Swiss AI Hub implementiert eine gestaffelte Datenaufbewahrungsstrategie, die zwischen temporären und permanenten
Daten unterscheidet. Zudem bietet die Plattform technische Mechanismen, um die Rechte betroffener Personen, insbesondere
das Recht auf Löschung, zu unterstützen. Jeder Löschvorgang wird im Audit-Trail nachvollziehbar erfasst.

### Technische Umsetzung im Swiss AI Hub: Ephemere Daten und DSGVO-APIs

- **Datenaufbewahrungsrichtlinien:** Die Plattform verwendet eine `gestaffelte Aufbewahrungsstrategie`. `Ephemere Daten`
  wie hochleistungs-Arbeitsspeicher oder ausführungsspezifische Daten, die für das Debugging benötigt werden, laufen
  nach 30 Tagen automatisch ab oder werden gelöscht. Workflow-Ereignisse in NATS JetStream werden ebenfalls mit
  zeitbasierten (30 Tage) und kapazitätsbasierten Limits (10 Millionen Nachrichten) verwaltet. Für
  `permanenten Speicher` (NoSQL) müssen Organisationen eigene Daten-Lifecycle-Richtlinien implementieren, um die
  Datenaufbewahrung gemäss ihren regulativen und geschäftlichen Anforderungen zu steuern.
- **Unterstützung des Löschrechts:** Das `Recht auf Löschung (Art. 17 DSGVO / Art. 32 revDSG)` wird durch Funktionen wie
  das Entfernen von Nutzern aus Konversations-Threads unterstützt. Automatisierte Löschprozesse stellen sicher, dass
  temporäre Daten nach 30 Tagen aus den Caches und Vektorspeichern entfernt werden.
- **Audit-Trails für Löschungen:** Obwohl Thread-Nachrichten und Audit-Protokolle unveränderlich bleiben, um die
  Integrität der Audit-Trails zu bewahren, dokumentiert die Plattform die Anweisung zur Löschung und das entsprechende
  Ergebnis. APIs für Benutzerprofile, Konversations-Threads und Audit-Logs stehen zur Verfügung, um Auskunftsrechten
  nachzukommen und die Nachweisbarkeit von Löschvorgängen zu gewährleisten.
- `UNKLARHEIT IN DER DOKU - BITTE PRÜFEN: Die Quelldokumentation erwähnt keine "Secure-Delete"-Funktion (physisches Überschreiben von Daten). Die effektive Entfernung hängt von der zugrundeliegenden Speichertechnologie ab und müsste dort explizit konfiguriert sein, um ein Überschreiben zu gewährleisten.`

## 7. Kontinuierliche Datenflussüberwachung und Data Loss Prevention (DLP)

Ein produktives KI-System erfordert eine lückenlose Überwachung aller Datenflüsse, um Anomalien und potenzielle
Sicherheitsvorfälle frühzeitig zu erkennen. Der Schutz vor Datenexfiltration (DLP) und eine effektive Reaktion auf
Sicherheitsvorfälle sind entscheidend, um die Integrität und Vertraulichkeit sensibler Unternehmensinformationen zu
wahren.

### Mehrwert und Nutzen: Proaktive Sicherheit und schnelle Reaktion

Die kontinuierliche Überwachung und Alarmierung schützt proaktiv vor Sicherheitsvorfällen und ermöglicht eine schnelle
Reaktion auf potenzielle Bedrohungen. Dies minimiert den Schaden bei Datenpannen und stärkt die Compliance des
Unternehmens. C-Level-Führungskräfte erhalten die Gewissheit, dass Datenflüsse transparent sind und ungewöhnliche
Aktivitäten sofort erkannt werden. IT-Sicherheitsteams können durch die zentrale Observability-Suite die
Systemintegrität in Echtzeit überwachen, Sicherheitslücken identifizieren und effektive Incident-Response-Prozesse
etablieren.

### Konzepte & Prozesse: Die Säulen der Observability und präventive Massnahmen

Die Plattform basiert auf den branchenüblichen Säulen der Observability (Health Checks, Metriken, Logs), um ein
umfassendes Bild der Systemaktivitäten zu liefern. Durch die Analyse dieser Daten können ungewöhnliche Muster im
Datenfluss erkannt und präventive Massnahmen wie die PII-Anonymisierung als erste Linie der Data Loss Prevention (DLP)
ergriffen werden.

### Technische Umsetzung im Swiss AI Hub: OpenTelemetry, SigNoz und Alerting

- **Umfassende Observability:** Das gesamte Überwachungs- und Alarmierungssystem des Swiss AI Hub basiert auf
  `OpenTelemetry (OTel)`. Ein zentraler `OpenTelemetry Collector` empfängt Logs, Metriken und Traces von allen Diensten,
  reichert diese mit Metadaten an und exportiert sie sicher an die gewählten Ziele. Als offiziell unterstütztes
  Observability-Backend dient `SigNoz`, das vereinheitlichte Dashboards für Infrastruktur, Anwendungsleistung und
  `KI-Operationen` (Modellnutzung, Token-Verbrauch, Kosten pro Operation) bietet.
- **Anomalieerkennung und DLP-Aspekte:** `Flexible Alarmierungsfunktionen` in SigNoz ermöglichen die Konfiguration von
  Benachrichtigungen für kritische Dienstausfälle, Leistungsverschlechterung, Ressourcenlimits, `Kostenmanagement`
  (ungewöhnlich hoher Token-Verbrauch) und `Sicherheitsereignisse` (z.B. wiederholte fehlgeschlagene Anmeldeversuche).
  Diese Alarme können an E-Mail, Slack oder Microsoft Teams weitergeleitet werden. Die `PII-Anonymisierung` durch
  Presidio fungiert als eine primäre, präventive DLP-Massnahme, indem sensible Daten vor dem Verlassen der Plattform
  geschwärzt werden. Darüber hinaus unterstützen `umfassende Audit-Trails`, die alle Zugriffsversuche und
  Berechtigungsprüfungen protokollieren, die forensische Analyse und die Erkennung verdächtiger Datenübertragungen.
- `UNKLARHEIT IN DER DOKU - BITTE PRÜFEN: Eine explizite "Data Loss Prevention"-Funktion (z.B. automatische Blockierung von Daten-Exports basierend auf Inhalt oder Volumen) über die PII-Anonymisierung und allgemeine Zugriffsüberwachung hinaus ist in der Quelldokumentation nicht detailliert beschrieben. Die Alarme können auf ungewöhnliche Muster hinweisen, aber eine automatische Blockierung des Datenflusses wird nicht explizit erwähnt.`
- **Sichere Log-Übertragung an SIEM:** Durch die OTel-Grundlage können Telemetriedaten sicher an alternative
  OTLP-kompatible Backends wie Grafana, Datadog oder Splunk (SIEM-Systeme) exportiert werden, indem lediglich die
  Collector-Konfiguration angepasst wird.
