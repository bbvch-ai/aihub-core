# Kapitel 05: Administration und Governance

## Zentrale Steuerung in einer dezentralen Realität

Mit der Einführung von KI-Systemen in die Unternehmenslandschaft verschiebt sich der Fokus zwangsläufig von der
technischen Machbarkeit hin zur operativen Beherrschbarkeit. Während die vorangegangenen Kapitel die Transparenz und
Datensouveränität beleuchteten, adressiert dieses Kapitel die Werkzeuge und Prozesse, die notwendig sind, um diese
Prinzipien im täglichen Betrieb durchzusetzen. Für IT-Leiter, Compliance-Verantwortliche und das C-Level stellt sich
nicht mehr die Frage, *ob* KI genutzt wird, sondern *wer* sie *wie*, in *welcher Qualität* und zu *welchen Kosten*
nutzen darf.

Eine unregulierte KI-Landschaft tendiert zur Entropie: Unklare Zugriffsberechtigungen führen zu Sicherheitslücken,
unüberwachte Kostenmodelle sprengen Budgets und mangelnde Qualitätssicherung erodiert das Vertrauen der Nutzer. Der
Swiss AI Hub begegnet diesen Herausforderungen mit einem zentralisierten Ansatz für Administration und Governance. Die
Plattform bietet ein einheitliches Kontrollzentrum, das Identitätsmanagement, granulare Zugriffskontrollen,
Budgetsteuerung und Qualitätsüberwachung integriert, ohne die Agilität der Fachabteilungen einzuschränken.

## Identitätsmanagement und nahtlose Integration

### Die Identität als neuer Perimeter

In modernen Enterprise-Architekturen ist nicht mehr das physische Netzwerk, sondern die digitale Identität der primäre
Sicherheitsperimeter. Die Einführung einer KI-Plattform darf daher keinesfalls den Aufbau einer parallelen
Benutzerverwaltung («Schatten-Verzeichnis») bedeuten. Isolierte Benutzerdatenbanken erhöhen nicht nur den
administrativen Aufwand, sondern stellen durch asynchrone Austrittsprozesse (Offboarding) ein erhebliches
Sicherheitsrisiko dar.

### Integration bestehender Verzeichnisdienste

Der Swiss AI Hub integriert sich nahtlos in die bestehende Identity-Provider-Landschaft (IdP) des Unternehmens. Die
Plattform implementiert Authentifizierung basierend auf den Industriestandards OpenID Connect (OIDC) und OAuth 2.0.
Anstatt eigene Passwörter zu speichern, delegiert das System die Überprüfung der Anmeldeinformationen an bewährte
Enterprise-Lösungen wie Microsoft Entra ID (Azure Active Directory), Keycloak oder andere OIDC-konforme Dienste.

Dies ermöglicht die sofortige und unternehmensweite Durchsetzung von Sicherheitsstandards. Wenn Ihre Organisation
Multi-Faktor-Authentifizierung (MFA) oder passwortlose Anmeldeverfahren (Passkeys) vorschreibt, gelten diese Richtlinien
automatisch auch für den Zugang zum Swiss AI Hub. Sitzungsdauer und Timeouts werden zentral gesteuert. Ein Mitarbeiter,
der im zentralen Verzeichnis deaktiviert wird, verliert im selben Moment den Zugriff auf alle Agenten-Profile und
Wissensdatenbanken, da die Plattform bei jeder Anfrage die Gültigkeit der Token (JWT) kryptografisch validiert.

## Granulare Zugriffskontrolle (RBAC) und dynamische Sichtbarkeit

### Das Prinzip der minimalen Rechte (Least Privilege)

Die pauschale Vergabe von Zugriffsrechten («Jeder sieht alles») ist in einem Umfeld, das potenziell Zugriff auf sensible
Personaldaten oder strategische Dokumente hat, inakzeptabel. Governance erfordert Präzision. Der Swiss AI Hub
implementiert hierfür ein hierarchisches, rollenbasiertes Zugriffskontrollsystem (RBAC), das sowohl auf der
Benutzeroberfläche als auch auf der API-Ebene greift.

Das System nutzt eine strukturierte Syntax in Punkt-Notation (`aihub.[user|admin].<service>.<resource>`), um
Berechtigungen exakt abzubilden. Diese Struktur erlaubt sowohl extreme Granularität als auch effiziente Verwaltung durch
Wildcards. Ein Administrator kann einer Abteilung mit einem einzigen Eintrag wie `aihub.user.agent.marketing.*` Zugriff
auf alle Marketing-Bots gewähren oder mittels `aihub.user.agent.>` den Zugriff auf alle Agenten-Ressourcen in beliebiger
Tiefe erlauben. Umgekehrt kann der Zugriff auf einen spezifischen Finanz-Agenten
(`aihub.user.agent.finance.budget_2024`) strikt auf den CFO und Controller beschränkt bleiben.

Diese Berechtigungslogik ist tief in der Architektur verankert («Defense in Depth»). Selbst wenn ein Nutzer die
Benutzeroberfläche umgehen würde, prüft der **Access Checker** im Backend bei jeder Anfrage die Berechtigungsvorlagen
gegen die Benutzerrolle. API-Endpunkte sind durch Controller geschützt, die dynamisch Pfadparameter auflösen und
validieren, sodass eine unautorisierte Ressourcenabfrage bereits auf Protokollebene scheitert.

### Sicherheit durch dynamische Dienstsichtbarkeit

Ein häufiges Problem komplexer Enterprise-Software sind überfrachtete Benutzeroberflächen, die Nutzern Funktionen
anzeigen, die sie gar nicht ausführen dürfen – oft resultierend in frustrierenden «Zugriff verweigert»-Meldungen. Der
Swiss AI Hub verfolgt hier den Ansatz der «Dynamischen Dienstsichtbarkeit».

Beim Start der Anwendung prüft das Backend den autorisierten Dienstkatalog des Nutzers. Die Benutzeroberfläche rendert
daraufhin ausschliesslich jene Elemente, für die eine explizite Berechtigung vorliegt. Ein Data Scientist sieht
Werkzeuge für Experimente und Evaluationen, während ein Sachbearbeiter im Kundendienst lediglich die für ihn relevanten
Support-Agenten sieht. Nicht autorisierte Dienste sind nicht nur ausgeblendet, sondern existieren für die Sitzung des
Nutzers faktisch nicht. Dieser Ansatz eliminiert Bedienungsfehler und reduziert die Angriffsfläche («Security through
Invisibility»), da potenzielle Angreifer keine Informationen über vorhandene, aber gesperrte Systemteile erhalten.

## Datenschutz-Compliance und Betroffenenrechte

### Unterstützung regulatorischer Anforderungen (DSGVO/DSG)

Unternehmen agieren bei der Nutzung der Plattform als Datenverantwortliche und müssen die Einhaltung von
Datenschutzgesetzen wie der DSGVO oder dem Schweizer DSG gewährleisten. Ein kritischer Aspekt hierbei ist die Wahrung
der Betroffenenrechte, insbesondere das Recht auf Löschung («Recht auf Vergessenwerden») und das Auskunftsrecht.

Der Swiss AI Hub unterstützt diese Anforderungen durch technische Massnahmen («Privacy by Design»). So werden ephemere
Daten, die keinen dauerhaften Geschäftswert haben, automatisch nach einer konfigurierbaren Frist (Standard: 30 Tage)
gelöscht. Für dauerhafte Daten, wie Benutzerprofile oder persistierte Chat-Verläufe, stellt die Plattform APIs bereit,
die Administratoren erlauben, gezielte Berichtigungen oder Löschungen vorzunehmen, ohne die Integrität der Audit-Trails
zu gefährden.

### Transparenz und Einwilligung

Um der Rechenschaftspflicht nachzukommen, protokolliert das System alle wesentlichen Verarbeitungsschritte. Dies
ermöglicht es Organisationen, Auskunftsersuchen effizient zu beantworten, indem Export-Funktionen für benutzerbezogene
Daten genutzt werden. Da die Plattform die Rechtsgrundlage der Verarbeitung (z. B. Einwilligung oder Vertragserfüllung)
nicht selbst festlegt, stellt sie die notwendigen Werkzeuge bereit, um den Status von Nutzern zu verwalten. Über die
RBAC-Steuerung können Zugriffe im Falle eines Widerspruchs sofort entzogen werden, was die Verarbeitung effektiv stoppt,
während die Datenbasis für gesetzliche Aufbewahrungspflichten erhalten bleibt.

## Wirtschaftliche Steuerung und Kostenkontrolle

### Transparenz in der Kostenstruktur

Der Betrieb von Large Language Models (LLMs) führt eine neue Kostenvariable in die IT-Budgets ein: die Token-basierte
Abrechnung. Da jede Interaktion – vom simplen «Hallo» bis zur Analyse eines 50-seitigen Dokuments – Kosten verursacht,
ist die Gefahr unkontrollierter Ausgaben («Bill Shock») real. Traditionelle Pauschalmodelle greifen hier nicht.

Der Swiss AI Hub bietet eine detaillierte Aufschlüsselung der Kostenstruktur. Das System unterscheidet zwischen
verschiedenen Token-Typen (Prompt, Completion, Embedding) und Modellklassen. Es macht transparent, dass ein
«Flaggschiff-Modell» (z.B. GPT-4-Klasse) für komplexe Denkaufgaben signifikant teurer ist als ein «effizientes Modell»
(z.B. GPT-4o-mini-Klasse), das für Klassifizierungsaufgaben oft völlig ausreicht. Diese Daten werden pro Konversation
erfasst und sind direkt im Thread einsehbar, was das Kostenbewusstsein der Nutzer schärft. Auch bei lokal gehosteten
Modellen (CAPEX-Modell) können fiktive Token-Preise hinterlegt werden, um die Ressourcennutzung intern vergleichbar zu
machen und eine Schatten-Rechnung (Shadow Accounting) zu ermöglichen.

### Budgetierung und Limits

Um Budgetsicherheit zu gewährleisten, ermöglicht die Plattform die Definition harter und weicher Limits über den
integrierten LiteLLM-Proxy. Administratoren können Obergrenzen auf Benutzer- oder Zeitebene festlegen, die durch
Umgebungsvariablen gesteuert werden:

- **Maximales Budget (Hard Limit):** Ein harter Deckel (konfigurierbar via `LITE_LLM_PROXY_USER_MAX_BUDGET`). Ist dieser
  erreicht, werden weitere Anfragen des Nutzers für den definierten Zeitraum (z.B. `30d`) blockiert.
- **Warnschwelle (Soft Limit):** Ein Schwellenwert (`LITE_LLM_PROXY_USER_SOFT_BUDGET`), der Benachrichtigungen auslöst,
  ohne den Betrieb zu stoppen, um frühzeitig intervenieren zu können.
- **Ratenbegrenzung (Rate Limiting):** Technische Drosselung von Tokens pro Minute (TPM) oder Anfragen pro Minute (RPM).
  Dies verhindert Missbrauch oder fehlerhafte Skripte, die in kurzer Zeit enorme Kosten verursachen könnten.

Diese Mechanismen ermöglichen eine verursachergerechte interne Verrechnung (Chargeback) und verhindern, dass einzelne
«Power-User» das Budget ganzer Abteilungen aufzehren.

## Qualitätssicherung und Bewertungs-Framework

### Vom «Bauchgefühl» zur messbaren Metrik

Governance beschränkt sich nicht auf Zugriff und Kosten, sondern umfasst zwingend die Ergebnisqualität. In einem
Unternehmenskontext muss verifizierbar sein, dass ein Agent korrekt, vollständig und prägnant antwortet. Das blosse
Vertrauen darauf, dass ein Modell «meistens gut klingt», ist kein tragfähiges Fundament für Geschäftsprozesse.

Der Swiss AI Hub integriert hierfür ein systematisches Bewertungs-Framework (Evaluations). Administratoren und
Entwickler können **Golden Datasets** anlegen – kuratierte Sammlungen von repräsentativen Fragen und idealen
Referenzantworten (Ground Truth). Automatisierte Experimente prüfen neue Versionen eines Agenten gegen diese Datensätze.
Dabei fungieren spezialisierte LLMs als neutrale «Richter», die die Antwort des Agenten mit der Referenz vergleichen und
Bewertungen auf einer Skala von 0 bis 5 Sternen in drei Dimensionen vergeben:

1. **Korrektheit:** Ist die Aussage faktisch richtig und frei von Halluzinationen oder Widersprüchen im Vergleich zur
   Referenz?
2. **Vollständigkeit:** Wurden alle Aspekte der Frage und impliziten Bedürfnisse beantwortet?
3. **Prägnanz:** Ist die Antwort effizient formuliert oder unnötig weitschweifig?

Dies ermöglicht ein empirisches Vorgehen («Test-Driven Development» für KI). Ein Agenten-Profil geht erst produktiv,
wenn es im Testlauf eine definierte Qualitätsstufe erreicht hat.

### Nutzer-Feedback und Elo-Ranking

Auch nach dem Deployment endet die Qualitätssicherung nicht. Die Plattform erlaubt es Nutzern, Antworten direkt im Chat
mittels «Daumen hoch» oder «Daumen runter» zu bewerten. Im «Arena-Modus» können Nutzer sogar blind Antworten
verschiedener Modelle vergleichen.

Dieses Feedback fliesst in eine zentrale Bestenliste ein, die auf einem Elo-Rating-System basiert – ähnlich wie im
Schachsport oder E-Sport. Diese Daten sind für die Governance von unschätzbarem Wert: Sie zeigen objektiv auf, welche
Modelle in der Praxis am besten performen. Dies liefert Indikatoren für notwendige Nachschärfungen an der
Wissensdatenbank (RAG) oder den System-Prompts und unterstützt datenbasierte Entscheidungen bei der Modellauswahl.

## Operative Überwachung (Monitoring & Alerting)

### Health Checks und Systemgesundheit

Ein Ausfall des KI-Systems kann kritische Geschäftsprozesse zum Erliegen bringen. Die operative Governance erfordert
daher eine lückenlose Überwachung der Systemgesundheit. Der Swiss AI Hub setzt auf einen mehrschichtigen Ansatz der
Observability:

- **Native Docker Checks** überwachen auf unterster Ebene, ob Prozess-Container laufen.
- **Anwendungsspezifische Health-Endpunkte** (`/health`) validieren darüber hinaus, ob Dienste tatsächlich bereit sind,
  Anfragen zu verarbeiten (Readiness Probes), und ob Abhängigkeiten wie Datenbanken erreichbar sind.

Jede Statusänderung wird protokolliert, was eine schnelle Reaktion bei Störungen ermöglicht.

### Duale Observability-Strategie mit OpenTelemetry

Um den administrativen Aufwand zu minimieren und «Monitoring-Silos» zu vermeiden, basiert die gesamte Telemetrie der
Plattform auf dem offenen Industriestandard OpenTelemetry (OTel). Ein zentraler **OpenTelemetry Collector** fungiert als
Datendrehscheibe, die Telemetriedaten von allen Diensten empfängt, anreichert und intelligent weiterleitet.

Die Plattform verfolgt dabei eine **Duale Observability-Strategie**, die unterschiedliche Zielgruppen bedient:

1. **Operatives Monitoring (via SigNoz):** Strukturierte Logs, Metriken und Traces werden standardmässig an **SigNoz**
   gesendet, das als offizielles Backend fungiert. Hier überwachen IT-Teams Infrastruktur-Metriken (CPU, RAM),
   Fehlerraten und die allgemeine Systemstabilität. Dank OTel können diese Daten jedoch auch problemlos an externe
   Systeme wie Datadog, Splunk oder Grafana ausgeleitet werden.
2. **LLM-Observability (via Phoenix):** Parallel dazu werden KI-spezifische Daten über eine dedizierte Pipeline an
   **Phoenix** gesendet. Dieses Tool ist spezialisiert auf die Analyse von LLM-Interaktionen und visualisiert
   Token-Verbrauch, Latenz pro Denkschritt, RAG-Retrieval-Qualität und Kosten.

Durch diese Trennung erhalten sowohl das IT-Operations-Team als auch die KI-Entwickler massgeschneiderte Einblicke, ohne
sich gegenseitig zu behindern, während die Datenhoheit vollständig beim Unternehmen verbleibt.
