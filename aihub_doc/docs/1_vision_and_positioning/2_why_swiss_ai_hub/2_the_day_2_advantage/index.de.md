---
title: Der "Day 2"-Vorteil
source_sha: 4f0010578a7b770c62309aac7edc98c14e18501b48b97a30ae918431d5b85758
---

# Der „Day 2“-Vorteil: Probleme, die wir bereits gelöst haben

Tag 1 ist die Demo. Der Prototyp funktioniert, Stakeholder sind beeindruckt und alle sind begeistert von KI. Tag 2 ist,
wenn die Realität zuschlägt. Der Prototyp muss zu einem Produktionssystem werden, und plötzlich stehen Sie vor Dutzenden
von Problemen, die die Demo nie angesprochen hat.

Der Swiss AI Hub wurde von Teams entwickelt, die den „Day 2“ bereits viele Male erlebt haben. Wir haben Lösungen für
diese Probleme direkt in die Plattform integriert, damit Sie sie nicht selbst lösen müssen.

## Authentifizierung und Zugriffssteuerung

**„Day 2“-Problem:** Ihr Prototyp verwendet einen fest codierten API-Schlüssel. Jetzt benötigen Sie
Benutzerauthentifizierung, Rollenverwaltung und Audit-Protokolle. Bauen Sie ein Benutzersystem von Grund auf neu?
Integrieren Sie es in Active Directory? Wie gehen Sie mit Service-Konten für automatisierte Prozesse um?

**Bereits gelöst:** Die Plattform umfasst eine Unternehmensauthentifizierung mit SSO/OAuth-Unterstützung. Verbinden Sie
sich einmal mit Ihrem Identitätsanbieter, und jede Komponente erbt die richtige Authentifizierung. Benutzer, Agents und
Prozesse authentifizieren sich alle über dasselbe System. Die rollenbasierte Zugriffssteuerung bestimmt, wer welche
Modelle verwenden, auf welche Daten zugreifen und welche Aktionen ausführen darf. Jede Interaktion wird mit
Benutzerzuordnung protokolliert.

## Kostenexplosion und -verfolgung

**„Day 2“-Problem:** Die Demo kostete 50
$ an API-Aufrufen. Die Produktionsnutzung durch 100 Mitarbeiter kostet im ersten Monat 50.000 $. Die Finanzabteilung
wünscht eine Kostenverrechnung nach Abteilung. Das Management wünscht Ausgabenlimits. Niemand weiß, welche Prompts die
Kosten verursachen.

**Bereits gelöst:** LiteLLM bietet eine vereinheitlichte Kostenverfolgung über alle Modell-Provider hinweg. Setzen Sie
Quoten pro Benutzer, Team oder global. Verfolgen Sie Ausgaben in Echtzeit-Dashboards. Sehen Sie genau, welche Agents,
Prompts und Benutzer Kosten verursachen. Exportieren Sie detaillierte Berichte für die Rückverrechnung. Automatische
Abschaltungen verhindern Budgetüberschreitungen.

## Multi-Modell-Komplexität

**„Day 2“-Problem:** Ihr Prototyp verwendet GPT-4. Für die Produktion werden unterschiedliche Modelle für verschiedene
Aufgaben benötigt: günstige Modelle für die Klassifizierung, leistungsstarke Modelle für die Analyse, spezialisierte
Modelle für Code. Die Verwaltung mehrerer API-Schlüssel, der Umgang mit verschiedenen Antwortformaten und die
Bewältigung von Ratenbegrenzungen wird zum Albtraum.

**Bereits gelöst:** Das LiteLLM Gateway bietet eine einzige Schnittstelle zu allen Modellen. Konfigurieren Sie Provider
einmal, dann referenzieren Sie Modelle mit einfachen Namen. Automatisches Fallback, wenn primäre Modelle nicht verfügbar
sind. Konsistentes Anforderungs-/Antwortformat unabhängig vom Provider. Ratenbegrenzung und Wiederholungslogik werden
automatisch gehandhabt.

## Datenaufnahmepipeline

**„Day 2“-Problem:** Die Demo funktionierte mit 10 handverlesenen Dokumenten. Die Produktion hat 10.000 Dokumente in
verschiedenen Formaten, die täglich aktualisiert werden. Sie benötigen Dokumenten-Parsing, Chunking-Strategien,
Embedding-Generierung und Vektorspeicherung. Plus den Umgang mit Updates, wenn sich Dokumente ändern.

**Bereits gelöst:** Dagster-Pipelines verarbeiten Dokumente automatisch aus konfigurierten Quellen. MinerU verarbeitet
PDFs, Office-Dateien und komplexe Formate. Intelligentes Chunking bewahrt die Dokumentenstruktur. Embeddings, generiert
mit konfigurierbaren Modellen. Milvus bietet Vektorspeicherung auf Produktionsniveau. Geänderte Dokumente lösen eine
automatische Neuverarbeitung aus.

## Observability und Debugging

**„Day 2“-Problem:** Die KI gibt eine falsche Antwort. Was ist passiert? Auf welche Dokumente hat sie sich bezogen? Was
war der tatsächlich an das Modell gesendete Prompt? Wie debuggen Sie ein System, bei dem jeder Lauf anders ist?

**Bereits gelöst:** Mehrere Observability-Ebenen sind integriert. Langfuse-Tracing zeigt jeden LLM-Aufruf mit Eingaben
und Ausgaben. Workflow-Ereignisse machen jeden Schritt sichtbar. Dagster bietet vollständige Pipeline-Linage.
OpenTelemetry verfolgt Systemmetriken. Wenn etwas schiefläuft, können Sie den gesamten Ausführungspfad verfolgen.

## Benutzeroberfläche und Zugriff

**„Day 2“-Problem:** Ihr Prototyp ist ein Python-Skript. Benutzer benötigen ein Web-Interface, Manager wollen
Dashboards, und jeder erwartet, dass es in Teams funktioniert. Bauen Sie eine React-App? Stellen Sie Frontend-Entwickler
ein? Erstellen Sie separate Schnittstellen für verschiedene Benutzertypen?

**Bereits gelöst:** Die Plattform umfasst ein produktionsbereites Chat-Interface mit Sprach-, Bild- und
Dokumentenunterstützung. Prozess-Cockpit für die Workflow-Teilnahme. Admin-Dashboard für die Systemverwaltung. Teams-
und Slack-Bots für Benutzer, die diese Kanäle bevorzugen. WebSocket-Streaming für Echtzeit-Updates. Alles mit demselben
Backend verbunden.

## Deployment und Skalierung

**„Day 2“-Problem:** Der Prototyp läuft auf einem Entwickler-Laptop. Die Produktion benötigt hohe Verfügbarkeit,
horizontale Skalierung und Updates ohne Ausfallzeiten. Wie containerisieren Sie alles? Wie handhaben Sie Service
Discovery? Wie verwalten Sie Konfigurationen über Umgebungen hinweg?

**Bereits gelöst:** Alles läuft in Containern mit Docker Compose für einfaches Deployment oder Kubernetes für
Skalierung. NATS Messaging ermöglicht automatische Service Discovery. Skalieren Sie, indem Sie mehrere Agent-Instanzen
ausführen. Konfiguration über Umgebungsvariablen. Health Checks und automatische Neustarts gewährleisten die
Verfügbarkeit.

## Tests und Qualitätssicherung

**„Day 2“-Problem:** Wie testen Sie KI-Systeme, die jedes Mal unterschiedliche Antworten geben? Wie stellen Sie sicher,
dass Änderungen die bestehende Funktionalität nicht beeinträchtigen? Wie validieren Sie das Agent-Verhalten vor dem
Produktions-Deployment?

**Bereits gelöst:** Das SDK bietet `AgentTestRunner` für deterministische Tests. BDD-Muster mit pytest-bdd zur
Verhaltensüberprüfung. Evaluierungs-Frameworks zur Messung der Genauigkeit anhand von Testdatensätzen.
Sandbox-Umgebungen für sichere Tests. Langfuse-Tracing für das Test-Debugging.

## Compliance und Governance

**„Day 2“-Problem:** Die Rechtsabteilung benötigt Audit-Trails. Compliance erfordert Daten-Linage. Die Sicherheit will
wissen, wer auf was zugegriffen hat. Datenschutzbestimmungen erfordern PII-Handling. Wie fügen Sie Governance zu einem
System hinzu, das nicht dafür konzipiert wurde?

**Bereits gelöst:** Umfassende Audit-Protokollierung verfolgt alle Aktionen. Daten-Linage von der Quelle bis zur
Antwort. Presidio bietet PII-Erkennung und -Anonymisierung. Konfigurierbare Datenaufbewahrungsrichtlinien.
Exportfunktionen für Compliance-Berichterstattung. Alles von Anfang an unter Berücksichtigung der Governance konzipiert.

## Integration mit bestehenden Systemen

**„Day 2“-Problem:** Der Prototyp ist eigenständig. Die Produktion muss sich mit SharePoint, SAP, Salesforce und
benutzerdefinierten Datenbanken integrieren. Jede Integration erfordert verschiedene Authentifizierungsmethoden,
Datenformate und Fehlerbehandlung.

**Bereits gelöst:** OpenAI-kompatible API für Tool-Kompatibilität. Webhook-Endpunkte für externe System-Trigger.
NATS-Ereignisse für benutzerdefinierte Integrationen. SharePoint-Konnektor enthalten. Erweiterbares Ressourcensystem zum
Hinzufügen neuer Integrationen. Standardmuster für Fehlerbehandlung und Wiederholungslogik.

## Versionsmanagement und Updates

**„Day 2“-Problem:** Der Prototyp hat keine Versionskontrolle. Die Produktion muss verfolgen, welche Version welches
Agents welche Ausgabe produziert hat. Updates müssen vor dem Deployment getestet werden. Rollback-Fähigkeit ist
unerlässlich.

**Bereits gelöst:** Git-basiertes Versionsmanagement für alle Komponenten. Getaggte Container-Images für jede Version.
Konfiguration als Code für reproduzierbare Deployments.

## Der kumulative Vorteil

Jedes gelöste „Day 2“-Problem spart Wochen oder Monate an Entwicklungszeit. Zusammen stellen sie Jahre an bereits
abgeschlossener Engineering-Arbeit dar. Hierbei geht es nicht um Funktionen, die Sie vielleicht irgendwann benötigen.
Dies sind Probleme, denen Sie definitiv begegnen werden, wenn Sie vom Prototyp zur Produktion übergehen.

Der Swiss AI Hub existiert, weil wir den „Day 2“ oft genug durchlebt haben, um zu wissen, was kommt. Anstatt diese
Probleme einzeln zu entdecken und nach Lösungen zu suchen, beginnen Sie mit einer Plattform, auf der sie bereits
behandelt werden. Ihr Team kann sich darauf konzentrieren, KI-Funktionen zu entwickeln, die für Ihr Unternehmen wichtig
sind, anstatt Infrastruktur neu aufzubauen, die bereits existieren sollte.
