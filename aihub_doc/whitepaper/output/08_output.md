# Sicherheitsarchitektur

Sicherheit ist im Kontext von Enterprise-KI kein nachgelagertes Feature, sondern das fundamentale Fundament. Ein System,
das tiefgreifende Einblicke in Unternehmenswissen gewährt und automatisierte Entscheidungen trifft, muss nach den
strengsten Standards gehärtet sein. Der Swiss AI Hub verfolgt hierbei keinen isolierten Ansatz, sondern integriert
Sicherheit ganzheitlich in jede Schicht der Plattform – von der physischen Infrastruktur über den Netzwerkverkehr bis
hin zur semantischen Analyse von KI-Prompts.

Dieses Kapitel detailliert die Sicherheitsarchitektur, die auf dem Prinzip der «Defense-in-Depth» (Verteidigung in der
Tiefe) basiert. Es beschreibt, wie Identitäten verwaltet, Daten kryptografisch geschützt und Angriffe proaktiv abgewehrt
werden, um die Vertraulichkeit, Integrität und Verfügbarkeit (CIA-Triade) zu gewährleisten.

## Auf einen Blick

- **Mehrschichtige Abwehr:** Ein Defense-in-Depth-Ansatz kombiniert Netzwerksicherheit, Container-Härtung und
  Applikationsschutz, um Angriffe durch redundante Barrieren abzuwehren.
- **Identitäts-Föderation:** Integration bestehender Enterprise-Identitäten (z.B. Entra ID) via OIDC und OAuth 2.0 mit
  Unterstützung für PKCE und Multi-Faktor-Authentifizierung.
- **Kryptografischer Schutz:** Durchgängige Verschlüsselung mittels TLS 1.2+ für Datenübertragung (Data-in-Transit) und
  Architekturkonzepte für LUKS-Volume-Verschlüsselung im Ruhezustand.
- **Semantische Firewalls:** Einsatz von «Input Guards» und «Output Guards» sowie Presidio zur Abwehr von Prompt
  Injections und zur Maskierung von PII auf Plattform-Ebene.
- **Härtung gegen KI-Vektoren:** Strikte Validierung von Datei-Uploads (MIME-Type-Check) und Blockierung von
  Path-Traversal-Angriffen schützen vor Malware und Sabotage.

## Mehrschichtige Abwehr und Netzwerk-Isolation

### Geschäftlicher Nutzen

Die Bedrohungslandschaft für IT-Infrastrukturen entwickelt sich rasant weiter. Herkömmliche Perimeter-Sicherheit, die
sich auf eine einzige Firewall verlässt, ist für moderne Anwendungen unzureichend. Unternehmen benötigen eine
Architektur, die davon ausgeht, dass einzelne Barrieren überwunden werden könnten, und deshalb redundante
Schutzmechanismen bereithält. Dies minimiert das Risiko eines erfolgreichen Einbruchs drastisch und begrenzt im
Ernstfall den Schadenradius («Blast Radius»). Für CIOs bedeutet dies eine widerstandsfähige Infrastruktur, die auch
gezielten Angriffen standhält und den unterbrechungsfreien Geschäftsbetrieb sichert.

### Konzeptioneller Ansatz

Das Sicherheitsmodell des Swiss AI Hub basiert auf dem Konzept der strikten Isolation und der minimalen Exposition.
Anstatt alle Dienste direkt dem Netzwerk auszusetzen, operiert die Plattform wie eine Festung mit einem einzigen, streng
bewachten Tor. Dahinterliegende Komponenten kommunizieren in abgeschotteten Segmenten. Selbst wenn ein Angreifer das
äussere Tor überwinden würde, stünde er vor weiteren verschlossenen Türen. Zudem folgt die Plattform dem Prinzip der
«Immutable Infrastructure»: Container werden bei Updates komplett neu gebaut und ersetzt, statt gepatcht zu werden, was
die Konsistenz der Sicherheitskonfigurationen garantiert.

### Technische Umsetzung im Swiss AI Hub

Technisch realisiert die Plattform dies durch eine Kombination aus Reverse Proxy, Container-Isolation und striktem
Netzwerk-Routing:

- **Single Entry Point:** Der gesamte eingehende Verkehr wird ausschliesslich über **Traefik** als Reverse Proxy
  geleitet. Nur die Ports 80 (HTTP) und 443 (HTTPS) sind nach aussen geöffnet; alle anderen Ports bleiben durch die
  Netzwerk-Firewall (NSG) blockiert.
- **Interne Netzwerke:** Backend-Dienste wie die Vektordatenbank, die API oder das LLM-Gateway laufen in isolierten
  Docker-Netzwerken. Sie sind von aussen nicht direkt adressierbar und akzeptieren nur Verkehr von authentifizierten
  internen Komponenten.
- **Container-Härtung:** Anwendungsprozesse werden konsequent als Nicht-Root-Benutzer (UID 1000, GID 1000) ausgeführt.
  Dies verhindert, dass eine Sicherheitslücke in der Applikation zu einer Übernahme des Host-Systems (Container Escape)
  führt.
- **Minimale Basis-Images:** Die Verwendung von minimalen Slim-Images reduziert die Angriffsfläche erheblich, da
  unnötige Systemwerkzeuge und potenzielle Schwachstellen aus dem Betriebssystem entfernt sind. Multi-Stage-Builds
  stellen sicher, dass keine Compiler oder Build-Tools in die Produktionsumgebung gelangen.

## Identitätsmanagement und Zugriffskontrolle

### Geschäftlicher Nutzen

Passwörter sind oft das schwächste Glied in der Sicherheitskette. Die Verwaltung separater Benutzerkonten für jede
Applikation erhöht nicht nur den administrativen Aufwand, sondern auch das Risiko von Passwort-Diebstahl und Phishing.
Unternehmen fordern daher eine nahtlose Integration in ihre bestehenden Identitätssysteme. Mitarbeiter sollen sich mit
ihren gewohnten Unternehmens-Zugangsdaten anmelden können (Single Sign-On), während Administratoren Zugriffe zentral
steuern und bei Austritt eines Mitarbeiters sofort entziehen können.

### Konzeptioneller Ansatz

Der Swiss AI Hub vermeidet die Speicherung von sensiblen Anmeldedaten. Stattdessen setzt die Architektur auf föderierte
Identitäten. Die Plattform vertraut einem externen Identity Provider (IDP) die Authentifizierung an und übernimmt selbst
nur die Autorisierung. Dies bedeutet, dass Sicherheitsrichtlinien des Unternehmens – wie die Pflicht zur
Multi-Faktor-Authentifizierung (MFA) oder konditionale Zugriffsregeln (z.B. nur von Firmen-Laptops) – automatisch auch
für den AI Hub gelten, ohne dass diese dort separat konfiguriert werden müssen.

### Technische Umsetzung im Swiss AI Hub

Die Umsetzung erfolgt strikt nach offenen Industriestandards, um maximale Kompatibilität zu gewährleisten:

- **Protokolle:** Die Plattform nutzt **OpenID Connect (OIDC)** und **OAuth 2.0**. Dies ermöglicht die Integration mit
  Microsoft Entra ID (Azure AD), Keycloak oder jedem anderen OIDC-konformen Provider. Für interaktive Anmeldungen wird
  der sichere Authorization Code Flow mit **PKCE** (Proof Key for Code Exchange) verwendet.
- **Token-Validierung:** Bei jedem API-Aufruf prüft das System die Gültigkeit des übermittelten JSON Web Tokens (JWT).
  Dabei werden kryptografische Signaturen (RSA-256) gegen die öffentlichen Schlüssel des Ausstellers (JWKS) validiert.
  Die Prüfung umfasst Aussteller, Zielgruppe, Ablaufzeit und Signaturintegrität.
- **Rollen-Mapping:** Benutzergruppen aus dem Active Directory werden über die Microsoft Graph API abgerufen und
  automatisch auf interne Rollen (wie *AgentVerwender-Rolle* oder *WissensVerwalter-Rolle*) abgebildet.
- **Audit-Fähigkeit:** Sicherheitsereignisse bei Authentifizierung und Autorisierung werden strukturiert protokolliert
  und können über OpenTelemetry-Schnittstellen überwacht werden, um Anomalien in Echtzeit zu erkennen.

## Schutz der Datenintegrität und Verschlüsselung

### Geschäftlicher Nutzen

Daten sind das Kapital des modernen Unternehmens. Ihr Schutz vor Diebstahl – sei es durch physische Entwendung von
Servern oder durch Abhören von Leitungen – ist essenziell für die Compliance (DSG/DSGVO) und den Erhalt von
Geschäftsgeheimnissen. Eine Enterprise-Architektur muss garantieren, dass Daten für Unbefugte unlesbar sind, egal wo sie
sich befinden. Dies schützt das Unternehmen vor Reputationsschäden und rechtlichen Konsequenzen im Falle eines
Sicherheitsvorfalls.

### Konzeptioneller Ansatz

Die Sicherheitsarchitektur erzwingt Verschlüsselung in zwei Zuständen: während der Übertragung (Data-in-Transit) und im
Ruhezustand (Data-at-Rest). Das Konzept sieht vor, dass keine Daten im Klartext über Netzwerkknoten gesendet oder auf
Festplatten geschrieben werden. Die Schlüsselverwaltung erfolgt dabei unabhängig von den Daten, was eine Rotation von
Schlüsseln ermöglicht, ohne die Datensätze neu schreiben zu müssen.

### Technische Umsetzung im Swiss AI Hub

- **Verschlüsselung im Transit:** Traefik erzwingt **TLS 1.2 oder TLS 1.3** für alle externen Verbindungen und
  implementiert HSTS (Strict-Transport-Security). Veraltete Protokolle werden abgelehnt. Zertifikate werden in
  Produktionsumgebungen automatisch via Let's Encrypt verwaltet oder können als eigene Unternehmenszertifikate
  hinterlegt werden. Auch die ausgehende Kommunikation zu externen Cloud-LLMs (z.B. Azure OpenAI) oder
  Identitätsanbietern erfolgt ausschliesslich über HTTPS.
- **Verschlüsselung im Ruhezustand:** Das Architekturkonzept für die Speicherung basiert auf Docker-Volumes, die mittels
  **LUKS (Linux Unified Key Setup)** verschlüsselt werden. Dies bietet eine AES-256-Verschlüsselung im XTS-Modus auf
  Blockebene für alle Datenbanken (PostgreSQL, Milvus) und Dateisysteme. Sollte eine Festplatte physisch aus dem
  Rechenzentrum entwendet werden, bleiben die Daten ohne den Entschlüsselungscode unlesbar.

## Anwendungs-Sicherheit und KI-Schutzschilde

### Geschäftlicher Nutzen

KI-Anwendungen sind neuen Angriffsvektoren ausgesetzt, die traditionelle Firewalls nicht erkennen. Angriffe wie «Prompt
Injection», bei denen Benutzer versuchen, die KI zu manipulieren, oder das Hochladen von mit Malware verseuchten
Dokumenten stellen ernsthafte Risiken dar. Zudem besteht die Gefahr, dass die KI unbeabsichtigt sensible Informationen
preisgibt. Ein robustes System muss daher nicht nur die Infrastruktur schützen, sondern auch die Inhalte verstehen und
filtern, die verarbeitet werden.

### Konzeptioneller Ansatz

Der Ansatz lautet «Validierung und Sanitisierung». Jede Eingabe – ob Text-Prompt oder Datei-Upload – wird als potenziell
gefährlich betrachtet. Bevor Daten verarbeitet werden, durchlaufen sie mehrere Filterstufen. Dies umfasst formale
technische Prüfungen sowie semantische Analysen auf zwei Ebenen: der Plattform-Ebene (für generellen PII-Schutz) und der
Agenten-Ebene (für spezifische Verhaltensregeln). Spezialisierte «Guards» fungieren als inhaltliche Firewalls.

### Technische Umsetzung im Swiss AI Hub

Die Plattform setzt spezifische Mechanismen gegen diese Bedrohungen ein:

- **Eingabevalidierung bei Dateien:** Uploads werden gegen eine strikte Whitelist von ca. 40 erlaubten Dateitypen
  geprüft. Dabei wird nicht nur die Dateiendung, sondern der tatsächliche MIME-Typ validiert, um Tarnversuche (MIME-Type
  Spoofing) zu entlarven. Dateinamen werden bereinigt, um Path-Traversal-Angriffe (z.B. `../../etc/passwd`) und
  Null-Byte-Injections zu verhindern.
- **Plattform-Ebene PII-Schutz (Presidio):** Auf Ebene des LLM-Gateways (LiteLLM) scannt **Presidio** alle Eingaben.
  Sensible Daten wie E-Mail-Adressen oder Kreditkartennummern werden erkannt und entweder maskiert (ersetzt durch
  Platzhalter wie `[PERSON]`) oder die Anfrage wird im «Blockierungsmodus» komplett abgelehnt, bevor sie einen externen
  Anbieter erreicht.
- **Agenten-Ebene Guards:**
  - **Eingangs-Schutzmechanismen:** Validieren, ob die Frage thematisch zum Agenten passt (Topic Guard) oder gegen
    Richtlinien verstösst.
  - **Ausgangs-Schutzmechanismen:** Prüfen die Antwort der KI. Der «Kontext-Ausreichend-Schutzmechanismus» verhindert
    Halluzinationen bei RAG-Anfragen. Ein spezialisierter PII-Guard auf dieser Ebene redigiert sensible Daten (wie
    Mitarbeiter-E-Mails), die eventuell aus internen Dokumenten abgerufen wurden, bevor sie dem Nutzer angezeigt werden
    (`[REDACTED]`).
