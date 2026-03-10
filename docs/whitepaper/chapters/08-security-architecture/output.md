# Sicherheitsarchitektur

In der Ära von Enterprise-KI ist Sicherheit kein nachgelagertes Merkmal, sondern das fundamentale Fundament jeder
vertrauenswürdigen Architektur. Ein System, das tiefgreifende Einblicke in geschäftskritisches Unternehmenswissen
gewährt, muss nach den strengsten Standards gehärtet sein. Der Swiss AI Hub verfolgt hierbei eine ganzheitliche
Strategie, welche die Sicherheit in jede Schicht der Plattform integriert – von der physischen Isolation über den
Netzwerkverkehr bis hin zur semantischen Filterung von KI-Inhalten.

Dieses Kapitel detailliert die Sicherheitsarchitektur, die konsequent dem Prinzip der «Defense-in-Depth» (Verteidigung
in der Tiefe) folgt. Es beschreibt, wie Identitäten föderiert, Daten kryptografisch geschützt und Angriffsvektoren
proaktiv neutralisiert werden, um die Vertraulichkeit, Integrität und Verfügbarkeit aller Informationen dauerhaft zu
gewährleisten.

## Auf einen Blick

- **Defense-in-Depth Architektur:** Ein mehrschichtiges Sicherheitsmodell kombiniert strikte Netzwerkisolation in fünf
  Zonen mit gehärteten Container-Umgebungen.
- **Unternehmenstaugliche Identitätsföderation:** Native Integration von Microsoft Entra ID via OIDC und OAuth 2.0
  inklusive PKCE für höchste Authentifizierungsstandards.
- **Lückenlose Datenverschlüsselung:** Erzwingung von TLS 1.2+ für den Datentransfer sowie LUKS-basierte Verschlüsselung
  für ruhende Daten («Data-at-Rest»).
- **KI-spezifische Schutzmechanismen:** Plattformweiter PII-Schutz mittels Presidio sowie granulare Eingangs- und
  Ausgangsfilter (Guards) auf Agenten-Ebene.
- **Automatisierte Validierung:** Strenge technische Filter blockieren Path-Traversal, Malware-Uploads und
  Prompt-Injections bereits am Netzwerkrand.

## Mehrschichtige Abwehr und Netzwerk-Isolation

### Geschäftlicher Nutzen

Die Bedrohungslandschaft für moderne IT-Infrastrukturen ist hochdynamisch und erfordert Schutzmassnahmen, die über eine
klassische Perimeter-Firewall hinausgehen. Unternehmen benötigen eine Architektur, die auch bei der Kompromittierung
einzelner Komponenten widerstandsfähig bleibt und den Schadensradius («Blast Radius») effektiv begrenzt. Für
Entscheidungsträger bedeutet dies die Sicherstellung der Business Continuity sowie den Schutz vor lateralen Bewegungen
von Angreifern innerhalb des Netzwerks. Eine robuste Isolation schützt zudem die Reputation, indem sie sicherstellt,
dass sensible Backend-Systeme niemals direkt dem öffentlichen Internet ausgesetzt sind.

### Konzeptioneller Ansatz

Der Swiss AI Hub implementiert eine strikte Segmentierung auf Netzwerk- und Prozessebene. Das Konzept basiert auf der
Annahme, dass kein Dienst implizit vertrauenswürdig ist (Zero-Trust). Statt einer flachen Netzwerkstruktur werden
Dienste in logische Sicherheitszonen unterteilt. Die Kommunikation zwischen diesen Zonen ist streng reglementiert und
folgt dem Prinzip der minimalen Rechtevergabe. Ergänzt wird dies durch eine «Immutable Infrastructure»-Strategie:
Container werden bei jedem Update vollständig ersetzt statt gepatcht, was eine konsistente und geprüfte
Sicherheitskonfiguration über alle Umgebungen hinweg garantiert.

### Technische Umsetzung im Swiss AI Hub

Die technische Realisierung basiert auf einer Isolation mittels fünf dedizierter Docker-Netzwerke:

- **Zoneneinteilung:** Die Netzwerke umfassen «Proxy» (externer Traffic via Traefik), «Backend» (Anwendungsdienste),
  «Data» (Datenbanken), «Storage» (Dateisysteme) und «Egress» (reiner ausgehender Internetverkehr).
- **Single Entry Point:** Traefik fungiert als einziger Ingress-Controller. Nur die Ports 80 und 443 sind nach aussen
  geöffnet. Alle Backend-Dienste wie das LLM-Gateway oder die Vektordatenbank bleiben für das Internet unsichtbar.
- **Egress-Härtung:** Das ausgehende Netzwerk für Dienste wie Web-Scraper ist so konfiguriert, dass die
  Inter-Container-Kommunikation (ICC) deaktiviert ist. Dies verhindert, dass ein kompromittierter Scraper andere interne
  Dienste angreifen kann.
- **Container-Sicherheit:** Alle Prozesse werden als Nicht-Root-Benutzer (UID/GID 1000) ausgeführt. Die Verwendung
  minimaler «Slim-Images» und Multi-Stage-Builds reduziert die Angriffsfläche, da unnötige Systemwerkzeuge und Compiler
  aus den Produktionsumgebungen entfernt werden.

## Identitätsmanagement und Zugriffskontrolle

### Geschäftlicher Nutzen

In einer Enterprise-Umgebung ist die fragmentierte Verwaltung von Benutzerzugängen ein erhebliches Sicherheits- und
Effizienzrisiko. Mitarbeitende fordern einen nahtlosen Zugriff via Single Sign-On (SSO), während die IT-Administration
eine zentrale Kontrolle über Berechtigungen und den sofortigen Entzug von Zugriffen bei Austritten sicherstellen muss.
Eine moderne Identitätsstrategie eliminiert die Gefahr schwacher Passwörter durch die Durchsetzung von
Multi-Faktor-Authentifizierung (MFA) und stellt sicher, dass jede Aktion innerhalb der Plattform einer eindeutigen
Identität zugeordnet werden kann.

### Konzeptioneller Ansatz

Der Swiss AI Hub nutzt föderierte Identitäten, um die Authentifizierung an bewährte Enterprise Identity Provider (IDP)
zu delegieren. Die Plattform selbst speichert keine Passwörter, sondern vertraut kryptografisch signierten Tokens. Die
Autorisierung ist strikt von der Authentifizierung getrennt: Während der IDP bestätigt, wer ein Benutzer ist, bestimmt
die Plattform basierend auf einem hierarchischen Rollensystem, was dieser Benutzer tun darf. Dies ermöglicht eine
feingranulare Steuerung, bei welcher der Zugriff auf Agenten-Profile und Wissensdatenbanken exakt auf die
organisatorische Rolle zugeschnitten ist.

### Technische Umsetzung im Swiss AI Hub

Die Umsetzung erfolgt konsequent über offene Industriestandards:

- **Protokolle:** Die Plattform implementiert OpenID Connect (OIDC) und OAuth 2.0. Für interaktive Anmeldungen wird der
  Authorization Code Flow mit PKCE (Proof Key for Code Exchange) verwendet, um Abfangversuche von Codes zu verhindern.
- **Integration:** Microsoft Entra ID (Azure AD) wird nativ unterstützt. Die Plattform ruft via Microsoft Graph API
  Profilinformationen und Gruppenmitgliedschaften ab, die automatisch auf interne Rollen wie die
  *WissensVerwalter-Rolle* gemappt werden.
- **Token-Validierung:** Jeder API-Aufruf erfordert einen gültigen JSON Web Token (JWT). Die Validierung erfolgt gegen
  die öffentlichen Schlüssel (JWKS) des Identity Providers, wobei Signatur, Aussteller, Zielgruppe und Ablaufzeit
  geprüft werden.
- **Audit-Protokollierung:** Alle Authentifizierungs- und Autorisierungsereignisse werden als strukturierte
  OpenTelemetry-Events erfasst. Dies schafft einen lückenlosen Audit-Trail für Compliance-Prüfungen und ermöglicht die
  Echtzeit-Überwachung von Anomalien.

## Kryptografische Absicherung und Datenintegrität

### Geschäftlicher Nutzen

Der Schutz der Vertraulichkeit von Unternehmensdaten ist im Kontext des Schweizer Datenschutzgesetzes (revDSG) eine
gesetzliche Pflicht. Datenverluste durch das Abhören von Netzwerkleitungen oder den physischen Diebstahl von
Speichermedien können existenzbedrohende finanzielle Folgen und Reputationsschäden nach sich ziehen. Eine durchgängige
Verschlüsselung stellt sicher, dass Informationen für unbefugte Dritte wertlos bleiben, selbst wenn physische oder
netzwerkbasierte Barrieren überwunden werden. Dies ist die Voraussetzung für das Vertrauen von Kunden und Partnern in
die digitale Integrität des Unternehmens.

### Konzeptioneller Ansatz

Die Sicherheitsstrategie erzwingt Verschlüsselung in allen Zuständen. Während der Übertragung («Data-in-Transit») wird
eine Punkt-zu-Punkt-Verschlüsselung zwischen Client, Plattform und externen Modellanbietern sichergestellt. Für ruhende
Daten («Data-at-Rest») sieht das Architekturkonzept eine vollständige Abstraktion der Speicherschicht vor. Die
Schlüsselverwaltung erfolgt unabhängig von den Datenbeständen, was eine regelmässige Schlüsselrotation ohne
Beeinträchtigung der Datenverfügbarkeit ermöglicht.

### Technische Umsetzung im Swiss AI Hub

- **Verschlüsselung im Transit:** Traefik erzwingt TLS 1.2 oder TLS 1.3 für alle Verbindungen. Veraltete Chiffren werden
  abgelehnt. HSTS (Strict-Transport-Security) sorgt dafür, dass Browser ausschliesslich verschlüsselte Verbindungen
  nutzen. Auch die Kommunikation zu LLM-Providern (z.B. Azure OpenAI) erfolgt ausschliesslich über HTTPS.
- **Verschlüsselung im Ruhezustand:** Das System nutzt Docker-Volumes, die mittels LUKS (Linux Unified Key Setup)
  verschlüsselt werden können. Dies bietet eine AES-256-Verschlüsselung auf Blockebene für PostgreSQL, Milvus und den
  Dokumentenspeicher SeaweedFS.
- **Sicherheits-Header:** Zur Abwehr von Web-Angriffen werden Header wie Content-Security-Policy (CSP) und
  X-Frame-Options gesetzt, die das Einbetten in fremde Frames und MIME-Typ-Vortäuschungen verhindern.
- **Integritätsprüfung:** Alle Verbindungen zu externen Diensten validieren die Zertifikatsketten gegen
  vertrauenswürdige Root-Zertifizierungsstellen, um Man-in-the-Middle-Angriffe auszuschliessen.

## Anwendungssicherheit und KI-Schutzschilde

### Geschäftlicher Nutzen

KI-Systeme führen neue Risikoklassen ein, die durch klassische Firewalls nicht abgedeckt werden. Manipulative Eingaben
(«Prompt Injections») können versuchen, interne Anweisungen zu extrahieren oder Filter zu umgehen. Zudem besteht die
Gefahr, dass Personenidentifizierbare Informationen (PII) unbeabsichtigt an Cloud-Modelle gesendet werden. Ein
umfassender Schutzmechanismus muss daher sowohl die technische Integrität (Malware-Schutz) als auch die semantische
Ebene (Inhaltsschutz) absichern. Dies ermöglicht es Unternehmen, die Innovationskraft grosser Sprachmodelle zu nutzen,
ohne die Kontrolle über den Informationsabfluss zu verlieren.

### Konzeptioneller Ansatz

Der Swiss AI Hub implementiert ein mehrstufiges Filtersystem aus «Input Guards» und «Output Guards». Jede Interaktion
wird als potenziell bösartig eingestuft, bis sie validiert ist. Auf Plattformebene werden Daten anonymisiert, bevor sie
den geschützten Bereich verlassen. Auf Agentenebene wird sichergestellt, dass die Antworten der KI qualitativ hochwertig
sind und keine sensiblen Daten aus internen Wissensdatenbanken preisgeben.

### Technische Umsetzung im Swiss AI Hub

Die Plattform kombiniert technische Validierung mit semantischer Analyse:

- **Eingabevalidierung:** Datei-Uploads werden gegen eine Whitelist von über 40 Typen geprüft. Der tatsächliche MIME-Typ
  wird validiert, um getarnte ausführbare Dateien zu blockieren. Dateinamen werden von Zeichen gereinigt, die
  Path-Traversal-Angriffe (`../`) ermöglichen könnten.
- **PII-Anonymisierung (Presidio):** Im LLM-Gateway scannt Presidio jeden Prompt. Im «Maskierungsmodus» werden Namen
  oder E-Mails durch Platzhalter wie `[PERSON]` ersetzt. Im «Blockierungsmodus» werden hochsensible Anfragen (z.B.
  Kreditkartennummern) sofort abgewiesen.
- **Agenten-Guards:** Spezialisierte Wächter prüfen die Interaktion. Der «Kontext-Ausreichend-Schutzmechanismus»
  verhindert Halluzinationen, indem er Antworten blockiert, die nicht durch Quellen in der Wissensdatenbank belegt sind.
  Ein PII-Guard auf der Ausgangsseite redigiert sensible Daten aus Agenten-Antworten zu `[REDACTED]`, bevor der Benutzer
  diese sieht.
- **Daten-Lifecycle:** Ephemere Daten in Caches und temporären Speichern werden nach 30 Tagen automatisch gelöscht, um
  die Datensparsamkeit gemäss revDSG technisch zu erzwingen.
