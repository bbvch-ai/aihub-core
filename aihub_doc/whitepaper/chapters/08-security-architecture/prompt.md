# Kapitel 08: Sicherheitsarchitektur

## Kapitelziel

Dieses Kapitel beschreibt das fundamentale Sicherheitskonzept der Plattform, welches auf einem durchgängigen
Defense-in-Depth-Ansatz basiert, um Infrastruktur, Netzwerke und Anwendungen gleichermaßen zu schützen. Es wird
dargelegt, wie eine mehrschichtige Abwehrstrategie die Vertraulichkeit, Integrität und Verfügbarkeit (CIA-Triade) von
Informationen sicherstellt, ohne von einer einzelnen Technologiekomponente abhängig zu sein. Der Fokus liegt auf den
systemischen Schutzmechanismen für Identitätsmanagement, Datenverschlüsselung und Angriffsprävention, die gemeinsam ein
widerstandsfähiges Sicherheitsniveau gewährleisten. Dabei wird aufgezeigt, wie die Architektur darauf ausgelegt ist,
schweizerische regulatorische Anforderungen und internationale Compliance-Standards nachhaltig zu erfüllen. Abschließend
verdeutlicht das Kapitel, wie proaktive Sicherheitsoperationen und Überwachungsmaßnahmen die Resilienz gegenüber sich
wandelnden Bedrohungslagen dauerhaft aufrechterhalten.

## Kernaussagen

- Mehrschichtige Abwehr (Defense-in-Depth): Das Sicherheitskonzept basiert auf einer Defense-in-Depth-Strategie, die
  Schutzmechanismen auf Netzwerk-, Infrastruktur- und Anwendungsebene kombiniert, um Angriffe durch redundante Barrieren
  effektiv abzuwehren.
- Kryptografische Absicherung: Die Architektur erzwingt eine durchgängige Verschlüsselung aller Daten im Ruhezustand
  (Data-at-Rest) sowie während der Übertragung (Data-in-Transit) unter Verwendung aktueller Industriestandards und eines
  strikten Schlüsselmanagements.
- Netzwerkisolation und Air-Gap: Zur Minimierung der Angriffsfläche unterstützt das System eine strikte
  Netzwerksegmentierung bis hin zum vollständigen Air-Gap-Betrieb, der kritische Komponenten physisch vom öffentlichen
  Internet isoliert.
- KI-spezifische Schutzschilde (Security Guards): Spezialisierte Security-Layer überwachen Eingaben auf KI-typische
  Angriffsvektoren wie Prompt-Injections oder Jailbreaking-Versuche und blockieren diese, bevor sie verarbeitende
  Modelle erreichen.
- Architektonischer Datenschutz: Integrierte Anonymisierungsdienste sorgen auf Architekturebene dafür, dass
  personenbezogene Daten (PII) automatisch maskiert werden, bevor sie an Backend-Systeme oder LLMs weitergeleitet
  werden.
- Integrationsfähige Authentifizierungsstandards: Die Plattform setzt auf offene Standards (OIDC, SAML) zur nahtlosen
  Einbindung in bestehende Enterprise-Identitätsmanagement-Systeme, um Multi-Faktor-Authentifizierung (MFA) und Single
  Sign-On (SSO) systemweit durchzusetzen.
- Kontinuierliche Validierung: Die Widerstandsfähigkeit der Sicherheitsarchitektur wird durch regelmäßige, unabhängige
  Penetrationstests und Sicherheitsaudits überprüft, um Schwachstellen proaktiv zu identifizieren und zu beheben.

## Umfang

max. 900 Wörter, 3 Seiten

## Business-Fragen, die das Kapitel beantwortet

- Wie schützt die Plattform vor unbefugtem Zugriff?
- Unterstützt die Plattform Enterprise-SSO (Azure AD, Keycloak)?
- Wie funktioniert Multi-Faktor-Authentifizierung?
- Wie werden API-Token sicher verwaltet?
- Wie granular sind Berechtigungsprüfungen?
- Sind Daten während der Übertragung verschlüsselt (SSL/TLS)?
- Werden gespeicherte Daten verschlüsselt (Data-at-Rest)?
- Wie werden Verschlüsselungsschlüssel verwaltet?
- Wird Verschlüsselung auf Datenbank-Ebene unterstützt (TDE)?
- Wie schützt die Plattform vor Injection-Angriffen (SQL, XSS, Command)?
- Werden hochgeladene Dokumente auf Malware gescannt?
- Wie wird verhindert, dass Benutzer Malware hochladen oder verbreiten?
- Welche Mechanismen gibt es gegen Prompt-Injection-Angriffe?
- Wie wird die Plattform vor DoS/DDoS-Angriffen geschützt?
- Was sind "Security Guards" und wie funktionieren sie?
- Wie sind Services untereinander isoliert?
- Welche Firewall-Mechanismen sind implementiert?
- Kann die Plattform komplett vom Internet isoliert betrieben werden (Air-Gapped)?
- Wie wird externer Zugriff gesichert?
- Wie erkennt die Plattform persönliche Informationen (PII) in Dokumenten?
- Werden sensible Daten vor LLM-Verarbeitung anonymisiert?
- Wie wird verhindert, dass Benutzer sensible Informationen in Prompts eingeben?
- Können Rückschlüsse auf interne Benutzer aus anonymisierten Daten gezogen werden?
- Wie wird sichergestellt, dass Nutzerdaten nicht für Modellverbesserung missbraucht werden?
- Wie ist die Daten-Isolation zwischen verschiedenen Mandanten (Multi-Tenancy)?
- Läuft das LLM auf isolierter und sicherer Infrastruktur?
- Können Daten an Dritte gelangen?
- Welche Netzwerk-Isolation gibt es zwischen Komponenten?
- Werden regelmäßige Penetrationstests durchgeführt?
- Wer führt Sicherheitsaudits durch (intern oder Dritte)?
- Wie werden Sicherheitslücken identifiziert und behoben?
- Wie wird kontinuierlich auf Bedrohungen überwacht?
- Gibt es definierte Incident-Response-Prozesse?
- Wie werden Security-Updates eingespielt?
