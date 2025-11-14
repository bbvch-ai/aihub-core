# Kapitel 09: Regulator ische Compliance

## Kapitelziel
Erklären Sie, wie die Plattform Schweizer und europäische regulatorische Anforderungen erfüllt, mit Fokus auf revDSG, GDPR und EU AI Act Vorbereitung (600 Wörter, 2 Seiten).


## Kapitelabgrenzung und Fokus

**WICHTIG - Fokus dieses Kapitels**: Regulatorische Compliance: revDSG, GDPR, EU AI Act. Konkrete Compliance-Mechanismen und wie sie technisch umgesetzt sind.

**Behandeln Sie NICHT** (wird in anderen Kapiteln abgedeckt):
- Deployment-Optionen und Datensouveränität-Konzept → siehe Kapitel Kapitel 03 (Datensouveränität)
- Technische Sicherheitsarchitektur → siehe Kapitel Kapitel 08
- Audit-Trails und Transparenz-Features → siehe Kapitel Kapitel 04 (Plattform-Transparenz)

**Struktur-Anforderung**: Technische Details (falls vorhanden) IMMER am Ende des Kapitels als klar gekennzeichneter "Technischer Exkurs" oder "Technische Umsetzung".

**WICHTIG**: Folgen Sie den Richtlinien in `general_prompt.md` für Textfluss, Struktur und Business-Fragen. Dieses Kapitel ist **kurz** (600 Wörter).

## Business-Dimensionen (Priorität für dieses Kapitel)
1. **DATENSCHUTZ** - ABSOLUT KRITISCH: revDSG, FADP, DSGVO, AI Act
2. **SICHERHEIT** - Sehr wichtig: Compliance-relevante Sicherheitskontrollen
3. **ZUKUNFTSSICHERHEIT** - Wichtig: Regulatory Roadmap, AI Act Preparedness

**HINWEIS**: Datenschutz ist Top-Priorität für Schweizer Organisationen - behandeln Sie diese Dimension besonders ausführlich.

**Behandeln Sie diese Dimensionen explizit** mit konkreten Antworten auf Business-Fragen.

## Themen und Inhalte

Beschreiben Sie folgende Compliance-Themen und deren geschäftlichen Nutzen:

- **Schweizer Datensouveränität**: Deployment-Optionen (On-Premise, Swiss Cloud, Swiss-hosted SaaS), Data-Residency-Garantien, isolierte Infrastruktur, kein Datenexport außerhalb definierter Grenzen, Air-Gap-Option für höchste Anforderungen
- **Schweizerisches Datenschutzgesetz (revDSG / FADP)**: Privacy-by-Design, Transparenzanforderungen, technische Unterstützung für Betroffenenrechte (Auskunft, Berichtigung, Löschung), Consent-Management-Mechanismen, vollständige Audit-Trails
- **GDPR-Compliance**: Data Subject Access Requests, Right to be Forgotten mit kompletten Löschungs-Workflows, Data Portability, Consent-Tracking, Data Protection Impact Assessment (DPIA) Support
- **EU AI Act Vorbereitung**: Transparenz durch Workflow-basierte Agents, Human-in-the-Loop-Mechanismen, Accuracy and Robustness Testing, vollständige Dokumentation, eingebaute Risk-Management-Safeguards
- **Ethische AI-Richtlinien**: Ausrichtung an Council of Europe AI-Konvention, Berücksichtigung Schweizer AI-Leitlinien, Responsible AI Principles (Transparenz, Fairness, Accountability)
- **Datenaufbewahrung und Löschung**: Konfigurierbare Retention Policies, automatische Ablauf-Fristen, manuelle Löschungs-Workflows, ordnungsgemäße Datenentfernung bei Kontolöschung
- **Mehrsprachigkeit**: UI in Deutsch, Englisch, Französisch, Italienisch; Multi-Language-Dokumentenverarbeitung; Compliance-Dokumentation in Schweizer Sprachen

Fokussieren Sie auf konkrete Compliance-Mechanismen, wie die Plattform regulatorische Anforderungen technisch umsetzt und wie Organisationen Compliance-Nachweise führen können.

## Business-Fragen, die das Kapitel beantwortet

1. Wie stellt die Plattform sicher, dass Daten die Schweiz nicht verlassen?
2. Welche Deployment-Optionen gibt es für Schweizer Datensouveränität?
3. Kann die Plattform komplett vom Internet isoliert betrieben werden (Air-Gap)?
4. Wo werden Daten physisch gespeichert und verarbeitet?

5. Erfüllt die Plattform die Anforderungen des revidierten Schweizer Datenschutzgesetzes?
6. Wie ist Privacy-by-Design in der Architektur verankert?
7. Wie werden Transparenzanforderungen (Art. 19 revDSG) erfüllt?
8. Wie unterstützt die Plattform Betroffenenrechte (Auskunft, Berichtigung, Löschung)?
9. Wie funktioniert Consent-Management für revDSG-Compliance?
10. Welche Audit-Trails existieren für Compliance-Nachweise?

11. Erfüllt die Plattform GDPR-Anforderungen?
12. Wie werden Data Subject Access Requests (DSAR) gehandhabt?
13. Wie funktioniert "Right to be Forgotten" (Art. 17 DSGVO)?
14. Unterstützt die Plattform Data Portability (Art. 20 DSGVO)?
15. Wie wird Consent gemäß GDPR getrackt und verwaltet?
16. Wie unterstützt die Plattform Data Protection Impact Assessments (DPIA)?

17. Ist die Plattform auf den EU AI Act vorbereitet?
18. Wie erfüllt die Plattform Transparenzanforderungen des AI Act?
19. Wie sind Human-in-the-Loop-Mechanismen implementiert?
20. Welche Dokumentation existiert für AI-Modelle und Training?
21. Welche Risk-Management-Mechanismen sind eingebaut?
22. Wie wird Accuracy und Robustness sichergestellt?

23. Folgt die Plattform ethischen AI-Richtlinien (Council of Europe, Schweiz)?
24. Wie werden Responsible AI Principles (Transparenz, Fairness, Accountability) umgesetzt?
25. Gibt es Mechanismen gegen AI-Bias?

26. Welche Datenaufbewahrungsfristen gelten?
27. Können Aufbewahrungsfristen konfiguriert werden?
28. Wie werden Daten automatisch gelöscht nach Ablauf?
29. Können Benutzer ihre Daten manuell löschen?
30. Wie wird ordnungsgemäße Datenlöschung bei Kontolöschung sichergestellt?

31. In welchen Sprachen ist die Plattform verfügbar?
32. Können mehrsprachige Dokumente verarbeitet werden?
33. Ist Compliance-Dokumentation in Schweizer Sprachen verfügbar?
