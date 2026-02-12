---
title: Blueprints & Profile
---

# Agent Blueprints & Profile

Die AI-Hub-Plattform trennt Agentendefinitionen von ihren Konfigurationen. Dadurch können Administratoren mehrere
angepasste Versionen desselben Agententyps erstellen, ohne Codeänderungen vornehmen zu müssen.

## Schlüsselkonzepte

### Agent Blueprint

Ein **Agent Blueprint** ist eine Vorlage, die definiert, was ein Agent tun kann:

- Die Workflow-Schritte, die er befolgt (welche Aktionen er ausführt)
- Die Arten von Eingaben, die er akzeptiert (Text, Dateien, Bilder)
- Die verfügbaren Konfigurationsoptionen (Modellauswahl, Parameter)
- Die Ereignisse, die er produziert (was er ausgibt)

Blueprints werden von Entwicklern erstellt und erscheinen automatisch in der Plattform, wenn Agenten online gehen. Sie
können einen Blueprint nicht über die Benutzeroberfläche ändern. Betrachten Sie Blueprints als schreibgeschützte
Vorlagen.

### Agent Profil

Ein **Agent Profil** ist eine konfigurierte Instanz eines Blueprints:

- Hat eine eindeutige Kennung (Agenten-ID)
- Hat einen benutzerdefinierten Namen, eine Beschreibung und ein Symbol
- Verwendet spezifische Einstellungen aus den Optionen des Blueprints
- Kann bestimmte Berechtigungen zugewiesen bekommen

Sie können mehrere Profile aus demselben Blueprint erstellen. Jedes Profil arbeitet unabhängig mit seiner eigenen
Konfiguration. Beispielsweise könnten Sie aus einem "RAG Agent"-Blueprint erstellen:

- "HR-Richtlinien-Agent"-Profil, konfiguriert für die Suche in der HR-Dokumentensammlung
- "Rechts-FAQ-Agent"-Profil, konfiguriert für die Suche in Rechtsdokumenten
- "IT-Support-Agent"-Profil, konfiguriert für die Suche in der IT-Wissensbasis

Jedes Profil ist ein separater Agent, mit dem Benutzer interagieren können.

## Blueprints verwalten

### Verfügbare Blueprints anzeigen

Navigieren Sie zu **Admin > Agenten > Blueprints**, um alle verfügbaren Agentenvorlagen zu sehen.

Jeder Blueprint zeigt:

- **Name**: Die Blueprint-Kennung
- **Beschreibung**: Was der Agent tut
- **Status**: Ob derzeit Instanzen online sind
- **Konfigurationsformular**: Die für Profile verfügbaren Einstellungen

### Blueprint-Status

Blueprints zeigen den Online-/Offline-Status an, je nachdem, ob kürzlich laufende Agenteninstanzen registriert wurden.
Ein Offline-Blueprint bedeutet, dass derzeit keine Agenten dieses Typs laufen, aber Sie können trotzdem Profile
erstellen und konfigurieren. Diese Profile werden aktiv, wenn der Agentendienst startet.

## Profile verwalten

### Ein neues Profil erstellen

1. Navigieren Sie zum gewünschten Blueprint
2. Klicken Sie auf **Profil erstellen**
3. Füllen Sie die erforderlichen Felder aus:
   - **Agenten-ID**: Eine eindeutige Kennung (Kleinbuchstaben, Zahlen, Unterstriche, Bindestriche)
   - **Name**: Anzeigename in den ausgewählten Sprachen
   - **Beschreibung**: Was dieses spezifische Profil tut
   - **Symbol**: Visuelle Kennung
4. Konfigurieren Sie die agentenspezifischen Einstellungen (Modell, Parameter usw.)
5. Klicken Sie auf **Speichern**

Das Profil ist sofort verfügbar. Benutzer mit entsprechenden Berechtigungen können damit interagieren.

### Ein Profil bearbeiten

1. Navigieren Sie zu **Admin > Agenten > Profile**
2. Suchen und wählen Sie das Profil
3. Klicken Sie auf **Bearbeiten**
4. Ändern Sie die Konfiguration
5. Klicken Sie auf **Speichern**

Änderungen gelten für neue Konversationen. Bestehende aktive Konversationen werden mit der vorherigen Konfiguration
fortgesetzt, bis sie abgeschlossen sind.

### Ein Profil löschen

1. Navigieren Sie zum Profil
2. Klicken Sie auf **Löschen**
3. Bestätigen Sie das Löschen

Das Löschen eines Profils entfernt seine Konfiguration. Historische Konversationsdaten mit diesem Profil werden für
Prüfungszwecke aufbewahrt. Der Blueprint bleibt für die Erstellung neuer Profile verfügbar.

## Konfigurationsoptionen

Die für jedes Profil verfügbaren Einstellungen hängen vom Blueprint ab. Häufige Konfigurationsoptionen umfassen:

### Modellauswahl

Wählen Sie, welches Sprachmodell der Agent verwendet. Die Optionen hängen davon ab, welche Modelle über Ihre
LiteLLM-Konfiguration verfügbar sind.

### Temperatur

Steuert die Kreativität der Antworten:

- Niedrigere Werte (0,0-0,3): Fokussiertere, deterministischere Antworten
- Höhere Werte (0,7-1,0): Kreativere, variiertere Antworten

### Wissensbasis

Für RAG-fähige Agenten wählen Sie aus, welche Dokumentensammlungen der Agent durchsuchen kann.

### System-Prompt

Einige Agenten erlauben die Anpassung des System-Prompts, um Verhalten und Persönlichkeit anzupassen.

## Berechtigungen

Der Zugriff auf Profile folgt dem Berechtigungssystem der Plattform:

- **Blueprint-Zugriff** (`aihub.admin.agent.{blueprint}.*`): Profile für einen bestimmten Blueprint verwalten
- **Profil-Zugriff** (`aihub.user.agent.{blueprint}.{profile_id}`): Ein bestimmtes Profil verwenden
- **Wildcard-Zugriff** (`aihub.user.agent.*.>`): Zugriff auf alle Agenten (typischerweise für Administratoren)

Siehe den Abschnitt [Zugriffsverwaltung](/platform/access_management) für Details zur Konfiguration von Berechtigungen.

## Best Practices

### Namenskonventionen

- Verwenden Sie beschreibende Profilnamen, die den Zweck angeben ("HR-Richtlinien-Assistent" nicht "RAG Agent 1")
- Halten Sie Agenten-IDs kurz, aber aussagekräftig (`hr_richtlinien`, `rechts_faq`)
- Fügen Sie die Zielgruppe in Beschreibungen ein ("Für Mitarbeiter mit HR-Fragen")

### Konfigurationsstrategie

- Beginnen Sie mit konservativen Einstellungen (niedrigere Temperatur, kleinere Kontextfenster)
- Testen Sie mit repräsentativen Fragen, bevor Sie breit ausrollen
- Erstellen Sie separate Profile für verschiedene Anwendungsfälle anstatt eines generischen Profils

### Lebenszyklus-Management

- Überprüfen Sie die Profilnutzung regelmässig durch Audit-Logs
- Stellen Sie unbenutzte Profile ein, um Verwirrung zu reduzieren
- Dokumentieren Sie Konfigurationsentscheidungen für den Wissensaustausch im Team
