---
title: Der 'Day 2'-Vorteil
source_sha: 1eb9535c15d57c04249fb08a40c2ce8b779d72cfe4a4ed679e5fe3b77fde79f2
---

# Der „Day 2“-Vorteil: Probleme, die wir bereits gelöst haben

Tag 1 ist die Demo. Der Prototyp funktioniert, Stakeholder sind beeindruckt, und alle sind begeistert von KI. An Tag 2
holt die Realität Sie ein. Der Prototyp muss zu einem Produktionssystem werden, und plötzlich stehen Sie vor Dutzenden
von Problemen, die die Demo nie angesprochen hat.

Der Swiss AI Hub wurde von Teams entwickelt, die den „Day 2“ bereits viele Male erlebt haben. Wir haben Lösungen für
diese Probleme direkt in die Plattform integriert, damit Sie sie nicht selbst lösen müssen.

## Authentifizierung und Zugriffskontrolle

**Das Day-2-Problem:** Ihr Prototyp verwendet einen fest codierten API-Schlüssel. Jetzt benötigen Sie Benutzer-
Authentifizierung, Rollenverwaltung und Audit-Protokolle. Bauen Sie ein Benutzersystem von Grund auf neu? Integrieren
Sie es mit Active Directory? Wie gehen Sie mit Dienstkonten für automatisierte Prozesse um?

**Bereits gelöst:** Die Plattform umfasst Unternehmensauthentifizierung mit SSO/OAuth-Unterstützung. Verbinden Sie sich
einmal mit Ihrem Identity Provider, und jede Komponente erbt die entsprechende Authentifizierung. Benutzer, Agenten und
Prozesse authentifizieren sich alle über dasselbe System. Die rollenbasierte Zugriffskontrolle bestimmt, wer welche
Modelle nutzen, auf welche Daten zugreifen und welche Aktionen ausführen darf. Jede Interaktion wird mit
Benutzerzuordnung protokolliert.

## Kostenexplosion und -verfolgung

**Das Day-2-Problem:** Die Demo kostete 50 $ an API-Aufrufen. Die Nutzung in der Produktion durch 100 Mitarbeiter kostet
im ersten Monat 50.000 $. Die Finanzabteilung möchte eine Kostenzuordnung nach Abteilung. Das Management möchte
Ausgabenlimits. Niemand weiß, welche Prompts die Kosten in die Höhe treiben.

**Bereits gelöst:** LiteLLM bietet eine vereinheitlichte Kostenverfolgung über alle Modell-Anbieter hinweg. Legen Sie
Kontingente pro Benutzer, Team oder global fest. Verfolgen Sie die Ausgaben in Echtzeit-Dashboards. Sehen Sie genau,
welche Agenten, Prompts und Benutzer Kosten verursachen. Exportieren Sie detaillierte Berichte zur Kostenverrechnung.
Automatische Stopps verhindern Budgetüberschreitungen.

## Multi-Modell-Komplexität

**Das Day-2-Problem:** Ihr Prototyp verwendet GPT-4. Die Produktion benötigt verschiedene Modelle für verschiedene
Aufgaben: günstige Modelle für die Klassifizierung, leistungsstarke Modelle für die Analyse, spezialisierte Modelle für
Code. Die Verwaltung mehrerer API-Schlüssel, der Umgang mit unterschiedlichen Antwortformaten und die Bewältigung von
Rate Limits wird zu einem Albtraum.

**Bereits gelöst:** Das LiteLLM-Gateway bietet eine einzige Schnittstelle zu allen Modellen. Konfigurieren Sie Anbieter
einmal, und referenzieren Sie Modelle dann mit einfachen Namen. Automatischer Fallback, wenn primäre Modelle nicht
verfügbar sind. Konsistentes Anfrage-/Antwortformat unabhängig vom Anbieter. Rate Limiting und Wiederholungslogik werden
automatisch gehandhabt.

## Datenaufnahme-Pipeline

**Das Day-2-Problem:** Die Demo funktionierte mit 10 handverlesenen Dokumenten. Die Produktion umfasst 10.000 Dokumente
in verschiedenen Formaten, die täglich aktualisiert werden. Sie benötigen Dokumenten-Parsing, Chunking-Strategien,
Einbettungsgenerierung und Vektorspeicherung. Plus die Handhabung von Updates, wenn sich Dokumente ändern.

**Bereits gelöst:** Dagster-Pipelines verarbeiten Dokumente aus konfigurierten Quellen automatisch. Docling verarbeitet
PDFs, Office-Dateien und komplexe Formate. Smartes Chunking bewahrt die Dokumentenstruktur. Einbettungen werden mit
konfigurierbaren Modellen generiert. Milvus bietet Vektorspeicherung auf Produktionsniveau. Geänderte Dokumente lösen
eine automatische Neuverarbeitung aus.

## Beobachtbarkeit und Fehlersuche

**Das Day-2-Problem:** Die KI gibt eine falsche Antwort. Was ist passiert? Welche Dokumente wurden referenziert? Was war
der tatsächlich an das Modell gesendete Prompt? Wie debuggen Sie ein System, bei dem jeder Lauf anders ist?

**Bereits gelöst:** Mehrere Ebenen der Beobachtbarkeit sind integriert. Phoenix Tracing zeigt jeden LLM-Aufruf mit
Eingaben und Ausgaben. Workflow-Events machen jeden Schritt sichtbar. Dagster bietet eine vollständige Pipeline- Linie.
OpenTelemetry verfolgt Systemmetriken. Wenn etwas schiefgeht, können Sie den gesamten Ausführungspfad nachverfolgen.

## Benutzeroberfläche und Zugang

**Das Day-2-Problem:** Ihr Prototyp ist ein Python-Skript. Benutzer benötigen eine Weboberfläche, Manager möchten
Dashboards, und jeder erwartet, dass es in Teams funktioniert. Bauen Sie eine React-App? Stellen Sie Frontend-
Entwickler ein? Erstellen Sie separate Schnittstellen für verschiedene Benutzertypen?

**Bereits gelöst:** Die Plattform umfasst eine produktionsreife Chat-Oberfläche mit Sprache, Bildern und Dokumenten. Ein
Prozess-Cockpit für die Workflow-Teilnahme. Ein Admin-Dashboard für die Systemverwaltung. Teams- und Slack-Bots für
Benutzer, die diese Kanäle bevorzugen. WebSocket-Streaming für Echtzeit-Updates. Alles mit demselben Backend verbunden.

## Bereitstellung und Skalierung

**Das Day-2-Problem:** Der Prototyp läuft auf dem Laptop eines Entwicklers. Die Produktion erfordert hohe Verfügbarkeit,
horizontale Skalierung und Updates ohne Ausfallzeiten. Wie containerisieren Sie alles? Wie handhaben Sie die Service
Discovery? Wie verwalten Sie Konfigurationen über verschiedene Umgebungen hinweg?

**Bereits gelöst:** Alles läuft in Containern mit Docker Compose für die einfache Bereitstellung oder Kubernetes für die
Skalierung. NATS-Messaging ermöglicht die automatische Service Discovery. Skalieren Sie durch das Ausführen mehrerer
Agenten-Instanzen. Konfiguration über Umgebungsvariablen. Health Checks und automatische Neustarts gewährleisten die
Verfügbarkeit.

## Testen und Qualitätssicherung

**Das Day-2-Problem:** Wie testen Sie KI-Systeme, die jedes Mal unterschiedliche Antworten geben? Wie stellen Sie
sicher, dass Änderungen die bestehende Funktionalität nicht beeinträchtigen? Wie validieren Sie das Verhalten von
Agenten vor der Produktionsbereitstellung?

**Bereits gelöst:** Das SDK bietet `AgentTestRunner` für deterministische Tests. BDD-Muster mit pytest-bdd zur
Verhaltensüberprüfung. Evaluierungs-Frameworks zur Messung der Genauigkeit anhand von Testdatensätzen. Sandbox-
Umgebungen für sicheres Testen. Phoenix Tracing zur Test-Fehlersuche.

## Compliance und Governance

**Das Day-2-Problem:** Die Rechtsabteilung benötigt Audit-Protokolle. Die Compliance erfordert Daten-Lineage. Die
Sicherheit möchte wissen, wer auf was zugegriffen hat. Datenschutzbestimmungen verlangen den Umgang mit PII. Wie fügen
Sie einem System, das nicht dafür konzipiert wurde, Governance hinzu?

**Bereits gelöst:** Eine umfassende Audit-Protokollierung verfolgt alle Aktionen. Daten-Lineage von der Quelle bis zur
Antwort. Presidio bietet PII-Erkennung und Anonymisierung. Konfigurierbare Datenaufbewahrungsrichtlinien.
Exportfunktionen für Compliance-Berichte. Alles von Anfang an mit Blick auf Governance entwickelt.

## Integration mit bestehenden Systemen

**Das Day-2-Problem:** Der Prototyp ist eigenständig. Die Produktion muss mit SharePoint, SAP, Salesforce und
benutzerdefinierten Datenbanken integriert werden. Jede Integration erfordert unterschiedliche
Authentifizierungsmethoden, Datenformate und Fehlerbehandlung.

**Bereits gelöst:** OpenAI-kompatible API für Tool-Kompatibilität. Webhook-Endpunkte für externe Systemtrigger. NATS-
Events für benutzerdefinierte Integrationen. SharePoint-Konnektor enthalten. Erweiterbares Ressourcensystem zum
Hinzufügen neuer Integrationen. Standardmuster für Fehlerbehandlung und Wiederholungslogik.

## Versionsverwaltung und Updates

**Das Day-2-Problem:** Der Prototyp hat keine Versionskontrolle. Die Produktion muss verfolgen, welche Version welchen
Agenten welche Ausgabe produziert hat. Updates müssen vor der Bereitstellung getestet werden. Die Rollback-Fähigkeit ist
unerlässlich.

**Bereits gelöst:** Git-basierte Versionskontrolle für alle Komponenten. Getaggte Container-Images für jede Version.
Konfiguration als Code für reproduzierbare Bereitstellungen.

## Der kumulierte Vorteil

Jedes gelöste Day-2-Problem spart Wochen oder Monate an Entwicklungszeit. Zusammen repräsentieren sie Jahre an bereits
abgeschlossener Engineering-Arbeit. Hier geht es nicht um Funktionen, die Sie vielleicht irgendwann benötigen werden.
Dies sind Probleme, denen Sie definitiv begegnen werden, wenn Sie vom Prototyp zur Produktion übergehen.

Der Swiss AI Hub existiert, weil wir den „Day 2“ oft genug erlebt haben, um zu wissen, was kommt. Anstatt diese Probleme
einzeln zu entdecken und hektisch nach Lösungen zu suchen, starten Sie mit einer Plattform, auf der sie bereits
behandelt werden. Ihr Team kann sich darauf konzentrieren, KI-Funktionen zu entwickeln, die für Ihr Unternehmen wichtig
sind, anstatt Infrastruktur neu aufzubauen, die bereits vorhanden sein sollte.
