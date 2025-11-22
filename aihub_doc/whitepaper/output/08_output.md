# Kapitel 08: Sicherheitsarchitektur

Die erfolgreiche und vertrauenswürdige Einführung von Künstlicher Intelligenz (KI) in Schweizer Unternehmen ist
untrennbar mit einer robusten Sicherheitsarchitektur verbunden. Angesichts strenger Datenschutzgesetze und dem
zunehmenden Aufkommen KI-spezifischer Bedrohungen ist ein systematischer, mehrschichtiger Schutz von Infrastruktur,
Daten und Anwendungen unerlässlich. Dieses Kapitel beleuchtet, wie der Swiss AI Hub ein umfassendes
Defense-in-Depth-Konzept implementiert, das von der Netzwerkschicht bis zur KI-Anwendung reicht, um die Vertraulichkeit,
Integrität und Verfügbarkeit von Informationen jederzeit zu gewährleisten und gleichzeitig höchste regulatorische
Anforderungen zu erfüllen.

## 1. Mehrschichtige Abwehr (Defense-in-Depth) als strategisches Fundament

### Mehrwert und Nutzen: Ganzheitlicher Schutz und nachhaltige Compliance

Für C-Level-Führungskräfte ist die Gewissheit entscheidend, dass KI-Investitionen auf einer resilienten und sicheren
Grundlage ruhen. Ein durchgängiger Defense-in-Depth-Ansatz minimiert nicht nur das Risiko von Datenlecks und
Systemausfällen, sondern sichert auch die Einhaltung kritischer regulatorischer Vorgaben wie dem revDSG und der DSGVO.
Dies fördert das Vertrauen in die KI-Systeme und schützt den Unternehmensruf. Für IT-Professionals bedeutet dies eine
konsistente Sicherheitsstrategie, die durch Redundanz die Widerstandsfähigkeit gegen komplexe Bedrohungen erhöht und die
Verwaltung durch die Nutzung bewährter Standards vereinfacht.

### Konzepte & Prozesse: Redundante Barrieren und risikobasiertes Design

Das Sicherheitskonzept des Swiss AI Hub basiert auf dem Prinzip der mehrschichtigen Abwehr, bei dem Schutzmechanismen
auf Netzwerk-, Infrastruktur- und Anwendungsebene kombiniert werden. Ziel ist es, Angriffe durch redundante Barrieren
effektiv abzuwehren und sicherzustellen, dass das Kompromittieren einer einzelnen Schutzschicht nicht zum vollständigen
Systemausfall oder Datenverlust führt. Jede Komponente der Architektur ist darauf ausgelegt, ihre spezifischen
Sicherheitsaufgaben zu erfüllen und dabei nahtlos mit den anderen Schichten zu interoperieren, um ein robustes
Gesamtsystem zu bilden.

### Technische Umsetzung im Swiss AI Hub: Eine integrierte Sicherheitsarchitektur

Der Swiss AI Hub realisiert dieses mehrschichtige Sicherheitsmodell durch das Zusammenspiel verschiedener technischer
Komponenten. Externe Zugriffe werden zunächst durch Netzwerk-Firewalls und einen Reverse Proxy gefiltert. Die internen
Dienste laufen in isolierten Docker-Containern mit minimalen Rechten. Authentifizierung und Autorisierung sichern den
Zugang zu Plattformressourcen, während Daten im Ruhezustand und während der Übertragung verschlüsselt sind. Ergänzt wird
dies durch KI-spezifische Eingabe- und Ausgabe-Wächter sowie Anonymisierungsfunktionen, die präventiv die Integrität und
Vertraulichkeit von KI-Interaktionen gewährleisten.

## 2. Identitäts- und Zugriffsmanagement: Sichere Authentifizierung und Autorisierung

### Mehrwert und Nutzen: Schutz vor unbefugtem Zugriff und nahtlose Benutzererfahrung

Für Schweizer Unternehmen ist der Schutz vor unbefugtem Zugriff von grösster Bedeutung. Der Swiss AI Hub bietet hierfür
eine robuste Lösung, die sich nahtlos in bestehende Enterprise-Identitätsmanagement-Systeme integriert. Dies ermöglicht
Single Sign-On (SSO) und Multi-Faktor-Authentifizierung (MFA) für erhöhte Sicherheit und eine reibungslose
Benutzererfahrung. Führungskräfte erhalten die Gewissheit, dass Zugriffe auf sensible Daten und KI-Funktionen streng
kontrolliert und auditierbar sind, während IT-Teams von einer zentralen Verwaltung und der Einhaltung etablierter
Standards profitieren.

### Konzepte & Prozesse: Standardisierte Protokolle und rollenbasierte Zugriffskontrolle

Die Plattform implementiert Authentifizierung und Autorisierung basierend auf den branchenüblichen Protokollen OpenID
Connect (OIDC) und OAuth 2.0. Dies gewährleistet Kompatibilität mit Enterprise Identity Providern wie Microsoft Entra ID
(Azure Active Directory) und ermöglicht die Delegation der Benutzerauthentifizierung. Die Autorisierung erfolgt über ein
hierarchisches, rollenbasiertes Zugriffskontrollmodell (RBAC), das das Prinzip der geringsten Rechte durchsetzt.

### Technische Umsetzung im Swiss AI Hub: JWT-Validierung und Entra ID Integration

Der Swiss AI Hub authentifiziert Benutzer über den OAuth 2.0 Authorization Code Flow mit PKCE. Jeder Benutzer erhält
einen JSON Web Token (JWT), dessen kryptografische Signatur mittels öffentlicher Schlüssel vom JWKS-Endpoint des
Identity Providers validiert wird. Für den API-Zugriff wird standardmässige OAuth 2.0 Bearer Token-Authentifizierung
unterstützt. Die Plattform ist primär mit Microsoft Entra ID integriert, um Benutzerprofile und Rollenzuweisungen
abzurufen. Autorisierungsentscheidungen werden serverseitig durch eine `AccessChecker`-Komponente getroffen, die für
jede API-Anfrage die zugewiesenen Rollen des Benutzers und die erforderlichen Berechtigungen evaluiert. Diese
Berechtigungen nutzen eine hierarchische Punkt-Notation mit Wildcard-Mustern (z.B. `aihub.user.agent.*`), um eine
feingranulare Steuerung zu ermöglichen.

## 3. Datenverschlüsselung: Schutz im Ruhezustand und während der Übertragung

### Mehrwert und Nutzen: Maximale Vertraulichkeit und regulatorische Konformität

Die durchgängige Verschlüsselung ist eine fundamentale Anforderung für den Schutz sensibler Unternehmensdaten. Der Swiss
AI Hub gewährleistet, dass Informationen sowohl im Ruhezustand (Data-at-Rest) als auch während der Übertragung
(Data-in-Transit) vor unbefugtem Zugriff geschützt sind. Dies erfüllt nicht nur die strengen Anforderungen des revDSG
und der DSGVO, sondern schützt auch vor Datendiebstahl und Manipulation, selbst bei physischem Zugriff auf
Speichermedien oder Abhören von Kommunikationskanälen.

### Konzepte & Prozesse: Zwei-Säulen-Verschlüsselung und robustes Schlüsselmanagement

Die Plattform nutzt ein zweistufiges Verschlüsselungskonzept. Alle persistent gespeicherten Daten sollen durch
vollständige Volume-Verschlüsselung geschützt werden. Gleichzeitig wird die gesamte Datenkommunikation, sowohl extern
als auch intern (wo kritisch), kryptografisch gesichert. Das Schlüsselmanagement erfolgt unabhängig von den Daten, um
Rotation und Sicherheit zu gewährleisten.

### Technische Umsetzung im Swiss AI Hub: LUKS-Verschlüsselung und TLS/HTTPS

- **Verschlüsselung im Ruhezustand (Data-at-Rest):** Das Sicherheitskonzept sieht eine **LUKS-Volume-Verschlüsselung**
  für alle persistenten Docker-Volumes vor (bei On-Premise-Deployments), die Anwendungsdatenbanken,
  Vektordatenbank-Indizes und Dokumentenspeicherung umfassen. Alternativ wird bei Private Cloud-Deployments
  `Azure Disk Encryption` verwendet. Dies bietet eine AES-256-Verschlüsselung im XTS-Modus und schützt Daten auch bei
  physischem Zugriff. Geheimnisse und sensitive Konfigurationsdaten werden über Umgebungsvariablen, Azure Key Vault oder
  Docker-Secrets verwaltet. UNKLARHEIT IN DER DOKU - BITTE PRÜFEN: Eine dedizierte Datenbank-Verschlüsselung auf Ebene
  Transparent Data Encryption (TDE) ist in der Quelldokumentation für die verwendeten Datenbanken nicht explizit
  aufgeführt, wird aber durch die LUKS-Volume-Verschlüsselung abgedeckt.
- **Verschlüsselung während der Übertragung (Data-in-Transit):** Der Traefik Reverse Proxy terminiert TLS am
  Netzwerkrand und erzwingt HTTPS mit TLS 1.2 und TLS 1.3. Er verwaltet auch Let's Encrypt-Zertifikate und wendet
  Sicherheits-Header wie HSTS an. Alle Verbindungen zu externen Diensten (z.B. LLM-Anbietern, OAuth/OIDC-Anbietern)
  nutzen HTTPS mit strikter Zertifikatsvalidierung. Echtzeit-Event-Streaming über WebSockets wird durch WSS (WebSocket
  Secure) mit Origin-Validierung gesichert. Die Kommunikation zwischen Docker-Containern im internen Docker-Netzwerk ist
  durch Netzwerkisolation geschützt, aber auf Anwendungsebene nicht standardmässig verschlüsselt.

## 4. Netzwerksicherheit und Isolation: Minimierung der Angriffsfläche

### Mehrwert und Nutzen: Strikte Segmentierung und Schutz vor externen Bedrohungen

Für Unternehmen ist die Minimierung der Angriffsfläche entscheidend, um die Plattform vor unautorisiertem Zugriff und
Cyberangriffen zu schützen. Der Swiss AI Hub implementiert eine strikte Netzwerksegmentierung und unterstützt
Betriebsmodi, die kritische Komponenten vom öffentlichen Internet isolieren können. Dies schützt vor DoS/DDoS-Angriffen
und gewährleistet eine hohe Resilienz. Die Möglichkeit, die Plattform in einer Air-Gapped-Umgebung zu betreiben, ist
besonders für Organisationen mit höchsten Sicherheitsanforderungen relevant.

### Konzepte & Prozesse: Default Deny und isolierte Dienstlandschaft

Das System verwendet eine standardmässige Ablehnungsrichtlinie (Default Deny Policy) auf Netzwerkebene und isoliert alle
internen Dienste in privaten Docker-Netzwerken. Ein einziger Reverse Proxy dient als kontrollierter Eintrittspunkt. Die
Architektur fördert zudem die Single-Tenant-Isolation, um eine strikte Trennung von Daten und Ressourcen pro
Organisation zu gewährleisten.

### Technische Umsetzung im Swiss AI Hub: Firewall, Traefik und Container-Isolation

Eine **Netzwerk-Firewall** (z.B. NSG) blockiert standardmässig alle Ports aus dem öffentlichen Internet, ausser 80 und
443\. **Traefik** fungiert als Reverse Proxy, dem einzigen extern zugänglichen Entry Point. Es terminiert TLS, wendet
Rate Limiting zum Schutz vor Brute-Force- und einfachen DoS-Angriffen an. Alle Anwendungsdienste (AI-Hub API, Web UI,
LiteLLM Proxy, Datenbanken) laufen in **isolierten Docker-Containern** in privaten Netzwerken. Jeder Container wird als
nicht privilegierter Benutzer ausgeführt (Nicht-Root-Benutzer) und nutzt Multi-Stage-Builds mit minimalen Basis-Images,
um die Angriffsfläche zu reduzieren. Regelmässige Basis-Image-Updates stellen sicher, dass die Container mit den
neuesten Sicherheitspatches versehen sind. Die Plattform kann auch in einer **Air-Gapped-Umgebung** betrieben werden,
sofern lokale LLMs verwendet werden (vergleiche Kapitel 03).

## 5. KI-spezifische Schutzmechanismen: Input/Output-Wächter und Datenanonymisierung

### Mehrwert und Nutzen: Verlässlichkeit und Schutz vor KI-Manipulation

Die zunehmende Komplexität von KI-Systemen erfordert spezielle Schutzmechanismen gegen Prompt-Injection, Jailbreaking
und Halluzinationen. Der Swiss AI Hub stellt durch KI-spezifische Schutzschilde sicher, dass die Modelle verlässlich und
im Einklang mit Unternehmensrichtlinien agieren. Eine automatische Anonymisierung schützt personenbezogene Daten (PII)
präventiv, bevor sie potenziell exponierenden Systemen zugeführt werden, was die Compliance und das Vertrauen in
KI-gestützte Prozesse stärkt.

### Konzepte & Prozesse: Agenten-Wächter und Privacy by Design

Die Plattform implementiert LLM-Wächter ("Guardrails"), die KI-Agenten-Interaktionen in Echtzeit überwachen – sowohl bei
der Eingabe (Input) als auch bei der Ausgabe (Output). Diese Wächter agieren auf Agenten-Ebene, um themenfremde
Anfragen, Richtlinienverstösse oder Halluzinationen zu verhindern. Eingangs-Schutzmechanismen analysieren
Benutzerfragen, bevor der Agent diese verarbeitet, während Ausgangs-Schutzmechanismen die generierten Agentenantworten
prüfen, bevor sie an den Benutzer ausgeliefert werden. Ergänzend dazu sorgt ein "Privacy by Design"-Ansatz durch die
Integration von Presidio auf Plattform-Ebene dafür, dass personenbezogene Daten (PII) proaktiv identifiziert und
anonymisiert werden, bevor sie externe LLM-Anbieter erreichen. Diese mehrstufige Verteidigung gewährleistet sowohl die
Integrität der Agenteninteraktionen als auch den umfassenden Schutz sensibler Benutzerdaten.

### Technische Umsetzung im Swiss AI Hub: Konfigurierbare LLM-Wächter und Presidio-Integration

Die **LLM-Wächter** umfassen spezialisierte Input- und Output-Schutzmechanismen. Bei den **Eingangs-Schutzmechanismen**
stellt der `Agentenbeschreibungs-Schutzmechanismus` sicher, dass Fragen zur definierten Funktion des Agenten passen und
blockiert irrelevante Anfragen. Der `Few-Shot-Schutzmechanismus` erzwingt benutzerdefinierte Richtlinien, indem er
Muster anhand von konfigurierbaren Beispielen lernt und ähnliche Anfragen blockiert oder zulässt. Die
**Ausgangs-Schutzmechanismen** umfassen den `Kontext-Ausreichend-Schutzmechanismus`, der prüft, ob der Agent über
genügend Informationen aus den Wissensdatenbanken verfügt, um präzise zu antworten und Halluzinationen entgegenwirkt.
Ein `Wächter für sensible Informationen` erkennt und redigiert vertrauliche oder personenbezogene Daten (PII) aus
Agentenantworten, bevor diese an Benutzer ausgeliefert werden, und ersetzt sie beispielsweise durch `[REDACTED]`.

Für die umfassende **Anonymisierung sensibler Daten (PII)** auf Plattform-Ebene integriert der Swiss AI Hub **Presidio**
in der LiteLLM-Proxy-Schicht. Presidio scannt Benutzerfragen nach PII-Mustern und erkennt dabei vordefinierte oder
benutzerdefinierte Entitätstypen wie:

- Personennamen
- E-Mail-Adressen
- Kreditkartennummern
- Telefonnummern
- Sozialversicherungsnummern (SSN)
- IP-Adressen
- Geografische Standorte
- Daten Die Erkennung erfolgt mittels Musterabgleich, regulären Ausdrücken und Modellen zur Erkennung benannter
  Entitäten (Named Entity Recognition) und unterstützt mehrere Sprachen, darunter Deutsch, Englisch, Französisch und
  Italienisch. Es bietet zwei Anonymisierungsmodi:
- **Maskierungsmodus (Mask mode):** Ersetzt erkannte PII durch Platzhalter (z.B. `[PERSON]`), um den Kontext für das LLM
  zu erhalten.
- **Blockierungsmodus (Block mode):** Lehnt die gesamte Anfrage ab, wenn hochsensible PII (z.B. Kreditkartennummern)
  erkannt werden. Diese Presidio-Guardrails sind standardmässig deaktiviert und müssen pro Deployment und
  Datensensitivitätsanforderung konfiguriert und aktiviert werden, um PII zu schützen, bevor sie externe LLM-Anbieter
  erreichen.

## 6. Robuste Eingabevalidierung und Integritätsschutz

### Mehrwert und Nutzen: Schutz vor Malware und Datenkorruption

Der Schutz der Wissensbasis vor bösartigen oder fehlerhaften Eingaben ist für die Sicherheit und Zuverlässigkeit jeder
KI-Plattform von höchster Bedeutung. Der Swiss AI Hub stellt sicher, dass nur sichere und erwartungsgemässe Inhalte in
das System gelangen, wodurch das Risiko von Malware-Einschleusung, Datenkorruption oder Systemkompromittierung minimiert
wird. Dies sichert die Integrität der Daten und die Verlässlichkeit der KI-Antworten.

### Konzepte & Prozesse: Strikte Whitelisting-Prinzipien und Validierungsregeln

Die Plattform setzt auf eine mehrstufige Eingabevalidierung für alle hochgeladenen Dokumente. Dies umfasst eine strikte
Whitelist für Dateitypen, eine Validierung des MIME-Typs sowie umfassende Prüfungen der Dateinamen und -grössen.

### Technische Umsetzung im Swiss AI Hub: Umfangreiche Validierungsmechanismen

Der Swiss AI Hub beschränkt Dateiuploads auf eine **Whitelist von etwa 40 genehmigten Dateierweiterungen**. Eine
**MIME-Typ-Validierung** verhindert das Verschleiern bösartiger Dateien. Dateinamen werden auf **Path
Traversal-Versuche** (`..`, `/`, `\`), Erweiterungs-Spoofing und Null-Bytes geprüft. **Dateigrössenbeschränkungen**
verhindern Ressourcenerschöpfung. Diese Massnahmen schützen vor SQL-, XSS- oder Command-Injection-Angriffen, indem
bösartige Dateiinhalte oder -namen abgeblockt werden. UNKLARHEIT IN DER DOKU - BITTE PRÜFEN: Die Quelldokumentation
beschreibt keine explizite Funktion für einen Malware-Scan während der Dokumentenaufnahme. Es wird angenommen, dass dies
eine ergänzende, organisatorische oder zukünftige technische Implementierung wäre.

## 7. Kontinuierliche Sicherheitsoperationen und Auditierung

### Mehrwert und Nutzen: Proaktive Bedrohungserkennung und revisionssichere Nachvollziehbarkeit

Die dynamische Bedrohungslandschaft erfordert eine kontinuierliche Überwachung und schnelle Reaktion auf
Sicherheitsvorfälle. Der Swiss AI Hub bietet eine umfassende Observability-Suite und lückenlose Audit-Trails, die eine
proaktive Bedrohungserkennung ermöglichen und die revisionssichere Nachvollziehbarkeit aller Systemaktivitäten
gewährleisten. Dies ist entscheidend für die Einhaltung von Compliance-Anforderungen und die Fähigkeit, auf
Sicherheitsvorfälle effektiv zu reagieren. Regelmässige Sicherheitsaudits und Penetrationstests überprüfen die
Widerstandsfähigkeit der Architektur.

### Konzepte & Prozesse: Observability-Säulen und Incident-Response-Fähigkeiten

Die Plattform basiert auf den branchenüblichen Säulen der Observability (Health Checks, Metriken, Logs, Traces), um ein
vollständiges Bild der Systemaktivitäten zu liefern. Alle Authentifizierungs- und Autorisierungsereignisse werden
lückenlos protokolliert. Dies bildet die Grundlage für eine effektive Incident Response und die kontinuierliche
Verbesserung der Sicherheitslage. Die Widerstandsfähigkeit wird durch regelmässige, unabhängige Penetrationstests und
Sicherheitsaudits überprüft.

### Technische Umsetzung im Swiss AI Hub: OpenTelemetry, SigNoz und Audit-Trails

Das gesamte Überwachungs- und Alarmierungssystem basiert auf **OpenTelemetry (OTel)**. Ein zentraler **OpenTelemetry
Collector** empfängt Logs, Metriken und Traces von allen Diensten und exportiert sie an **SigNoz** als offiziell
unterstütztes Observability-Backend. SigNoz bietet Dashboards für Infrastruktur, KI-Operationen, Anwendungsleistung und
Log-Analyse. Flexible Alarmierungen für kritische Dienstausfälle, Leistungseinbussen, Ressourcenlimits, Kostenmanagement
(ungewöhnlich hoher Token-Verbrauch) und Sicherheitsereignisse (z.B. fehlgeschlagene Anmeldeversuche) können
konfiguriert werden. Telemetriedaten können auch an alternative OTLP-kompatible Backends wie SIEM-Systeme (z.B. Splunk)
exportiert werden.

Jede Authentifizierungs- und Autorisierungsentscheidung sowie jede Benutzeraktion generiert detaillierte
**Audit-Log-Einträge**. Diese umfassen Benutzeridentität, angeforderte Ressourcen und Zugriffsentscheidungen.
Regelmässige Basis-Image-Updates der Container stellen sicher, dass die Plattform stets mit den neuesten
Sicherheitspatches ausgestattet ist und Sicherheitslücken proaktiv behoben werden. Die Existenz definierter
Incident-Response-Prozesse und die Planung regelmässiger Penetrationstests und Sicherheitsaudits (intern und extern)
sind Teil der organisatorischen Verpflichtung, die kontinuierliche Validierung der Sicherheitsarchitektur zu
gewährleisten.
