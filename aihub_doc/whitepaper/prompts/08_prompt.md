# Kapitel 08: Sicherheitsarchitektur

## Kapitelziel
Erklären Sie die mehrschichtige Sicherheitsarchitektur der Plattform mit Fokus auf konkrete Schutzmechanismen und wie sie Schweizer Organisationen vor Bedrohungen schützen (900 Wörter, 3 Seiten).

**WICHTIG**: Folgen Sie den Richtlinien in `general_prompt.md` für Textfluss, Struktur und Business-Fragen. Dieses Kapitel ist **mittel** (900 Wörter).

## Business-Dimensionen (Priorität für dieses Kapitel)
1. **SICHERHEIT** - SEHR WICHTIG: E2E-Verschlüsselung, Zero-Trust, Network Security, Angriffsprävention
2. **DATENSCHUTZ** - Sehr wichtig: Data-at-Rest, Data-in-Transit, Key Management, PII-Protection
3. **INTEGRATION** - Wichtig: Enterprise SSO, Security Monitoring, API-Security

**Behandeln Sie diese Dimensionen explizit** mit konkreten Antworten auf Business-Fragen.

## Themen und Inhalte

Beschreiben Sie folgende Sicherheitsthemen und deren geschäftlichen Nutzen:

- **Authentifizierung und Autorisierung**: Enterprise SSO (OAuth2/OIDC mit Azure AD, Keycloak), Multi-Faktor-Authentifizierung, API-Token-Management, Session-Management, feinkörnige Berechtigungsprüfung
- **Datenschutz und Verschlüsselung**: SSL/TLS für Datenübertragung, Data-at-Rest-Encryption, Transparent Data Encryption (TDE), Disk Encryption, Key Management (Azure Key Vault, HSM)
- **Input-Validierung und Angriffsprävention**: Schutz gegen Injection-Angriffe (SQL, Command, XSS), Malware-Scanning bei Dokument-Upload, APT-Detection, Prompt-Injection-Defense, Rate-Limiting, Security Guards für Agent-Validierung
- **Netzwerksicherheit**: Container-Isolation, Network Policies, Firewall-Regeln (Ingress/Egress), Reverse Proxy (Traefik), Air-Gapped Deployment für sensible Umgebungen
- **Datenschutz und Anonymisierung**: PII-Detection mit Presidio-Integration, Anonymisierung vor LLM-Verarbeitung, Prompt-Privacy-Mechanismen, Multi-Tenant-Architektur mit strikter Tenant-Trennung
- **Security Operations**: Regelmäßige Penetrationstests durch Drittanbieter, Sicherheitsaudits, Vulnerability Management, Security Monitoring, Incident-Response-Prozesse

Fokussieren Sie auf Defense-in-Depth-Ansatz, konkrete Schutzmechanismen und wie diese Schweizer Compliance-Anforderungen (revDSG, ISO 27001) erfüllen.

## Business-Fragen, die das Kapitel beantwortet

### Authentifizierung und Zugriff
1. Wie schützt die Plattform vor unbefugtem Zugriff?
2. Unterstützt die Plattform Enterprise-SSO (Azure AD, Keycloak)?
3. Wie funktioniert Multi-Faktor-Authentifizierung?
4. Wie werden API-Token sicher verwaltet?
5. Wie granular sind Berechtigungsprüfungen?

### Verschlüsselung
6. Sind Daten während der Übertragung verschlüsselt (SSL/TLS)?
7. Werden gespeicherte Daten verschlüsselt (Data-at-Rest)?
8. Wie werden Verschlüsselungsschlüssel verwaltet?
9. Wird Verschlüsselung auf Datenbank-Ebene unterstützt (TDE)?

### Angriffsprävention
10. Wie schützt die Plattform vor Injection-Angriffen (SQL, XSS, Command)?
11. Werden hochgeladene Dokumente auf Malware gescannt?
12. Wie wird verhindert, dass Benutzer Malware hochladen oder verbreiten?
13. Welche Mechanismen gibt es gegen Prompt-Injection-Angriffe?
14. Wie wird die Plattform vor DoS/DDoS-Angriffen geschützt?
15. Was sind "Security Guards" und wie funktionieren sie?

### Netzwerksicherheit
16. Wie sind Services untereinander isoliert?
17. Welche Firewall-Mechanismen sind implementiert?
18. Kann die Plattform komplett vom Internet isoliert betrieben werden (Air-Gapped)?
19. Wie wird externer Zugriff gesichert?

### Datenschutz und Anonymisierung
20. Wie erkennt die Plattform persönliche Informationen (PII) in Dokumenten?
21. Werden sensible Daten vor LLM-Verarbeitung anonymisiert?
22. Wie wird verhindert, dass Benutzer sensible Informationen in Prompts eingeben?
23. Können Rückschlüsse auf interne Benutzer aus anonymisierten Daten gezogen werden?
24. Wie wird sichergestellt, dass Nutzerdaten nicht für Modellverbesserung missbraucht werden?
25. Wie ist die Daten-Isolation zwischen verschiedenen Mandanten (Multi-Tenancy)?

### Isolierte Infrastruktur
26. Läuft das LLM auf isolierter und sicherer Infrastruktur?
27. Können Daten an Dritte gelangen?
28. Welche Netzwerk-Isolation gibt es zwischen Komponenten?

### Security Operations
29. Werden regelmäßige Penetrationstests durchgeführt?
30. Wer führt Sicherheitsaudits durch (intern oder Dritte)?
31. Wie werden Sicherheitslücken identifiziert und behoben?
32. Wie wird kontinuierlich auf Bedrohungen überwacht?
33. Gibt es definierte Incident-Response-Prozesse?
34. Wie werden Security-Updates eingespielt?

## Relevante RFP-Anforderungen

Während des natürlichen Schreibens sicherstellen, dass das Kapitel diese Anforderungen addressiert:

- **"Enterprise SSO (OAuth2/OIDC, Azure AD, Keycloak)"** ✓
- **"Multi-Faktor-Authentifizierung (MFA)"** ✓
- **"SSL/TLS-Verschlüsselung für Datenübertragung"** ✓
- **"Data-at-Rest-Encryption"** ✓
- **"Transparent Data Encryption (TDE)"** ✓
- **"Key Management (Azure Key Vault, HSM)"** ✓
- **"Schutz gegen Injection-Angriffe (SQL, XSS, Command)"** ✓
- **"Malware-Scanning und APT-Detection"** ✓
- **"Prompt-Injection-Defense"** ✓
- **"Rate-Limiting gegen DoS/DDoS"** ✓
- **"Container-Isolation und Network Policies"** ✓
- **"Firewall-Regeln (Ingress/Egress)"** ✓
- **"Air-Gapped Deployment-Option"** ✓
- **"PII-Detection und Anonymisierung (Presidio)"** ✓
- **"Multi-Tenant-Isolation"** ✓
- **"LLM auf isolierter und sicherer Infrastruktur"** ✓
- **"Regelmäßige Penetrationstests durch Drittanbieter"** ✓
- **"Vulnerability Management und Patch-Management"** ✓
- **"Security Monitoring und Incident Response"** ✓
