# Kapitel 08: Sicherheitsarchitektur

## Das Prinzip der mehrschichtigen Verteidigung (Defense-in-Depth)

In der modernen IT-Sicherheit hat sich die Erkenntnis durchgesetzt, dass kein einzelner Schutzmechanismus unfehlbar ist.
Dies gilt insbesondere für KI-Plattformen, die nicht nur klassischen Angriffen auf die Infrastruktur ausgesetzt sind,
sondern auch neuartigen Bedrohungen wie Prompt-Injections oder semantischen Manipulationen begegnen müssen. Eine
einfache Firewall am Netzwerkrand reicht nicht mehr aus, um komplexe Interaktionen zwischen Benutzern, Modellen und
sensiblen Daten zu schützen.

Der Swiss AI Hub verfolgt konsequent die Strategie der «Defense-in-Depth» (Verteidigung in der Tiefe). Anstatt sich auf
einen harten Perimeter und einen weichen Kern zu verlassen, wird jede Ebene des Technologie-Stacks als eigenständige
Sicherheitszone betrachtet. Von der physischen Infrastruktur über das Netzwerk und die Identität bis hin zur Validierung
der KI-Eingaben greifen redundante Sicherheitskontrollen. Sollte eine Barriere überwunden werden, verhindern
nachgelagerte Schichten eine Kompromittierung des Gesamtsystems und gewährleisten die Vertraulichkeit, Integrität und
Verfügbarkeit der Daten.

## Netzwerksicherheit und Infrastruktur-Härtung

### Isolation und kontrollierte Zugänge

Für Unternehmen ist die Kontrolle der Angriffsfläche entscheidend. Offene Ports und ungesicherte interne Dienste sind
Einfallstore für Angreifer. Der Swiss AI Hub reduziert diese Fläche auf ein absolutes Minimum durch eine strikte
«Default Deny»-Politik.

In der technischen Umsetzung fungiert Traefik als alleiniger Reverse Proxy und zentraler Eintrittspunkt («Ingress»). Nur
die Ports 80 (HTTP, mit automatischer Weiterleitung) und 443 (HTTPS) sind aus dem öffentlichen Netzwerk erreichbar. Alle
Anwendungsdienste – von der API über die Datenbanken bis zum LLM-Gateway – laufen in einem isolierten, privaten
Docker-Netzwerk. Diese Backend-Komponenten sind niemals direkt dem Internet ausgesetzt. Traefik terminiert die
Verbindungen, prüft Zertifikate und leitet nur validierte Anfragen an die internen Dienste weiter. Diese Architektur
verhindert effektiv den direkten Zugriff auf Datenbanken oder Service-Schnittstellen von aussen.

### Verschlüsselung und Verbindungssicherheit

Daten müssen sowohl im Ruhezustand als auch während der Übertragung geschützt sein. Der Swiss AI Hub setzt für den
externen Datenverkehr (Data-in-Transit) zwingend auf Verschlüsselung mittels TLS 1.2 oder 1.3. Veraltete oder unsichere
Cipher-Suites sind deaktiviert. Sicherheits-Header wie HSTS (Strict-Transport-Security) erzwingen, dass Browser und
Clients ausschliesslich verschlüsselte Verbindungen aufbauen können, und schützen so vor Man-in-the-Middle-Angriffen.

Für die interne Kommunikation setzt die Plattform auf strikte Netzwerksegmentierung. Da der Verkehr zwischen den
Containern das Host-System nicht verlässt, liegt der Fokus hier auf Isolation. Für gespeicherte Daten (Data-at-Rest) ist
das Sicherheitskonzept darauf ausgelegt, Verschlüsselung auf Volume-Ebene mittels LUKS (Linux Unified Key Setup) zu
nutzen. Die Architektur sieht vor, persistente Daten wie Datenbanken und Vektor-Indizes mit AES-256 im XTS-Modus zu
verschlüsseln. Dies stellt sicher, dass physisch entwendete Datenträger oder Snapshots nicht ausgelesen werden können,
da die Schlüsselverwaltung getrennt von den Daten erfolgt.

## Identitätszentrierte Sicherheit und Authentifizierung

### Integration in Enterprise-Verzeichnisdienste

Die Identität hat den klassischen Netzwerk-Perimeter als primäre Sicherheitsbarriere abgelöst. Die Verwaltung lokaler
Benutzerkonten ist fehleranfällig und skaliert schlecht in grossen Organisationen. Daher verzichtet der Swiss AI Hub auf
eine proprietäre Benutzerverwaltung zugunsten offener Industriestandards.

Die Plattform implementiert Authentifizierung basierend auf OpenID Connect (OIDC) und dem OAuth 2.0 Framework. Dies
ermöglicht eine nahtlose Integration in bestehende Identity Provider (IdP) wie Microsoft Entra ID (ehemals Azure AD),
Keycloak oder Okta. Der Anmeldeprozess nutzt dabei den sicheren «Authorization Code Flow» mit PKCE (Proof Key for Code
Exchange), um auch auf öffentlichen Clients höchste Sicherheit zu gewährleisten. Unternehmensrichtlinien für Passwörter,
Multi-Faktor-Authentifizierung (MFA) und Single Sign-On (SSO) werden somit automatisch auf den Swiss AI Hub angewendet.
Die Validierung erfolgt über kryptografisch signierte JSON Web Tokens (JWT), deren Signatur bei jeder Anfrage gegen die
öffentlichen Schlüssel (JWKS) des IdP geprüft wird.

### Entkoppelte Autorisierung

Authentifizierung (Wer bin ich?) und Autorisierung (Was darf ich?) sind im System strikt getrennt. Nach der
erfolgreichen Anmeldung ermittelt die Plattform die Zugriffsrechte dynamisch anhand der zugewiesenen Rollen und
Gruppenmitgliedschaften aus dem Microsoft Graph oder dem entsprechenden IdP. Dieses rollenbasierte
Zugriffskontrollsystem (RBAC) stellt sicher, dass Benutzer nur auf jene Ressourcen und Agenten-Profile zugreifen können,
für die sie explizit autorisiert sind. Selbst API-Zugriffe für technische Nutzer erfolgen über zeitlich begrenzte
Bearer-Tokens, was das Risiko langlebiger statischer Passwörter eliminiert.

## Container- und Applikationssicherheit

### Minimierung der Privilegien und Angriffsfläche

Sicherheit beginnt bereits beim Bau der Software. Veraltete Bibliotheken oder unnötige Systemwerkzeuge in Containern
erhöhen das Risiko von Schwachstellen. Der Swiss AI Hub begegnet dem durch gehärtete Container-Images und strikte
Laufzeitbeschränkungen.

Alle Dienste laufen konsequent als nicht privilegierte Benutzer (UID 1000, «Non-Root»). Sollte es einem Angreifer
gelingen, eine Anwendung zu kompromittieren, verhindern die fehlenden Root-Rechte einen Ausbruch aus dem Container
(«Container Escape») oder die Manipulation des Host-Systems. Die Container selbst basieren auf minimalen «Slim»-Images,
die durch Multi-Stage-Builds erzeugt werden. Dabei werden Compiler und Build-Werkzeuge nicht in die Produktionsumgebung
übernommen, was die Angriffsfläche drastisch reduziert. Updates erfolgen nach dem Prinzip der unveränderlichen
Infrastruktur: Container werden nicht gepatcht, sondern vollständig durch neue, sichere Versionen ersetzt.

### Strikte Eingabevalidierung

Neben Netzwerkangriffen stellen bösartige Inhalte ein erhebliches Risiko dar. Der Swiss AI Hub implementiert eine
tiefgreifende Eingabevalidierung, um Angriffe wie Path Traversal oder das Einschleusen von Malware zu verhindern.

Datei-Uploads werden gegen eine strikte Whitelist von ca. 40 genehmigten Dateitypen geprüft, darunter Dokumentformate
(PDF, DOCX), Bildformate und strukturierte Daten (JSON). Entscheidend ist dabei nicht nur die Dateiendung, sondern die
Validierung des tatsächlichen MIME-Typs, um Tarnversuche («Extension Spoofing») zu entlarven. Dateinamen werden
automatisch bereinigt, um Manipulationen am Dateisystempfad mittels Sonderzeichen oder Null-Bytes zu unterbinden. Zudem
schützen Grössenbeschränkungen auf Ebene des Reverse Proxies vor Ressourcenerschöpfung durch Denial-of-Service-Attacken.

## KI-spezifische Schutzschilde (AI Guardrails)

### Schutz vor Prompt-Injection und semantischen Angriffen

Klassische Sicherheitslösungen sind oft blind gegenüber Angriffen in natürlicher Sprache. Ein Angreifer könnte
versuchen, durch geschicktes «Jailbreaking» die Sicherheitsrichtlinien eines Modells zu umgehen.

Der Swiss AI Hub adressiert diese Lücke durch spezialisierte Eingangs-Schutzmechanismen (Input Guards). Diese operieren
direkt auf der Ebene der Agenten-Architektur. Ein «Agentenbeschreibungs-Schutzmechanismus» validiert semantisch, ob eine
Benutzerfrage überhaupt zum Aufgabenbereich des Bots passt, und weist themenfremde Anfragen ab. Ergänzend definieren
«Few-Shot-Schutzmechanismen» durch Beispiele erwünschtes und unerwünschtes Verhalten, sodass das System lernt, Angriffe
proaktiv zu erkennen.

### Anonymisierung und Ausgabekontrolle

Zum Schutz vor Datenabfluss ist im zentralen LLM-Gateway (LiteLLM) Microsoft Presidio integriert. Diese Komponente
scannt Prompts auf Personenidentifizierbare Informationen (PII) wie Kreditkartennummern oder E-Mail-Adressen, bevor sie
an ein Modell gesendet werden. Je nach Konfiguration werden diese Daten maskiert («Mask Mode») oder die Anfrage wird bei
hochsensiblen Daten blockiert («Block Mode»).

Auf der Ausgabeseite prüfen «Output Guards» die generierten Antworten. Bei Systemen mit Retrieval-Augmented Generation
(RAG) verhindert der «Kontext-Ausreichend-Schutzmechanismus» Halluzinationen, indem er Antworten unterdrückt, wenn die
Faktenlage in der Wissensdatenbank zu dünn ist. Zusätzlich werden sensible Daten, die aus internen Dokumenten stammen
könnten, in der Antwort geschwärzt («Redacting»), um unbeabsichtigte Informationslecks zu verhindern.

## Kontinuierliche Validierung und Resilienz

Sicherheit ist kein statischer Zustand, sondern ein fortlaufender Prozess. Die Architektur des Swiss AI Hub ist auf
Transparenz und Überprüfbarkeit ausgelegt. Durch die Integration in OpenTelemetry-Standards werden alle
sicherheitsrelevanten Ereignisse – von der Authentifizierung bis zur Token-Validierung – strukturiert protokolliert.
Dies ermöglicht Security Operations Centers (SOC), Anomalien in Echtzeit zu erkennen. Regelmässige Updates der
Basis-Images und die architektonische Trennung von Daten und Code gewährleisten, dass das System auch gegen neuartige
Bedrohungen resilient bleibt.
