```markdown
---
title: Blueprints & Profile
source_sha: "d876fc523f77179579f03b75c94d744a78dd5c29de0e0d0ae03bcb778ec6b8bd"
---

# Agent-Blueprints & Profile

Die Swiss AI Hub Plattform trennt Agent-Definitionen von deren Konfigurationen. Dies ermöglicht Administratoren, mehrere angepasste Versionen desselben Agent-Typs zu erstellen, ohne Codeänderungen vornehmen zu müssen.

## Schlüsselkonzepte

### Agent-Blueprint

Ein **Agent-Blueprint** ist eine Vorlage, die definiert, was ein Agent tun kann:

- Die Workflow-Schritte, denen er folgt (welche Aktionen er ausführt)
- Die Arten von Eingaben, die er akzeptiert (Text, Dateien, Bilder)
- Die verfügbaren Konfigurationsoptionen (Modellauswahl, Parameter)
- Die Ereignisse, die er erzeugt (was er ausgibt)

Blueprints werden von Entwicklern erstellt und erscheinen automatisch in der Plattform, wenn Agents online gehen. Sie können einen Blueprint nicht über die Benutzeroberfläche ändern. Betrachten Sie Blueprints als schreibgeschützte Vorlagen.

### Agent-Profil

Ein **Agent-Profil** ist eine konfigurierte Instanz eines Blueprints:

- Hat einen eindeutigen Bezeichner (Agent-ID)
- Hat einen benutzerdefinierten Namen, eine Beschreibung und ein Icon
- Verwendet spezifische Einstellungen aus den Optionen des Blueprints
- Können spezifische Berechtigungen zugewiesen werden

Sie können mehrere Profile aus demselben Blueprint erstellen. Jedes Profil arbeitet unabhängig mit seiner eigenen Konfiguration. Zum Beispiel könnten Sie aus einem „RAG Agent"-Blueprint Folgendes erstellen:

- „HR-Richtlinien-Agent"-Profil, konfiguriert für die Suche in der HR-Dokumentensammlung
- „Rechtliche FAQ-Agent"-Profil, konfiguriert für die Suche in rechtlichen Dokumenten
- „IT-Support-Agent"-Profil, konfiguriert für die Suche in der IT-Wissensdatenbank

Jedes Profil ist ein separater Agent, mit dem Benutzer interagieren können.

## Blueprints verwalten

### Verfügbare Blueprints anzeigen

Navigieren Sie zu **Admin > Agents > Blueprints**, um alle verfügbaren Agent-Vorlagen anzuzeigen.

Jeder Blueprint zeigt an:

- **Name**: Der Blueprint-Bezeichner
- **Beschreibung**: Was der Agent tut
- **Status**: Ob Instanzen derzeit online sind
- **Konfigurationsformular**: Die für Profile verfügbaren Einstellungen

### Blueprint-Status

Blueprints zeigen den Online-/Offline-Status basierend darauf an, ob sich kürzlich laufende Agent-Instanzen registriert haben. Ein Offline-Blueprint bedeutet, dass keine Agents dieses Typs derzeit ausgeführt werden, Sie können aber weiterhin Profile erstellen und konfigurieren. Diese Profile werden aktiv, sobald der Agent-Service startet.

## Profile verwalten

### Neues Profil erstellen

1. Navigieren Sie zu dem Blueprint, den Sie verwenden möchten
2. Klicken Sie auf **Profil erstellen**
3. Füllen Sie die erforderlichen Felder aus:
   - **Agent-ID**: Ein eindeutiger Bezeichner (Kleinbuchstaben, Zahlen, Unterstriche, Bindestriche)
   - **Name**: Anzeigename in den ausgewählten Sprachen
   - **Beschreibung**: Was dieses spezifische Profil tut
   - **Icon**: Visueller Bezeichner
4. Konfigurieren Sie die Agent-spezifischen Einstellungen (Modell, Parameter usw.)
5. Klicken Sie auf **Speichern**

Das Profil wird sofort verfügbar. Benutzer mit entsprechenden Berechtigungen können damit interagieren.

### Profil bearbeiten

1. Navigieren Sie zu **Admin > Agents > Profiles**
2. Suchen und wählen Sie das Profil aus
3. Klicken Sie auf **Bearbeiten**
4. Ändern Sie die Konfiguration
5. Klicken Sie auf **Speichern**

Änderungen werden für neue Konversationen wirksam. Bestehende aktive Konversationen werden mit der vorherigen Konfiguration fortgesetzt, bis sie abgeschlossen sind.

### Profil löschen

1. Navigieren Sie zum Profil
2. Klicken Sie auf **Löschen**
3. Bestätigen Sie die Löschung

Das Löschen eines Profils entfernt dessen Konfiguration. Historische Konversationsdaten mit diesem Profil bleiben zu Prüfzwecken erhalten. Der Blueprint bleibt für die Erstellung neuer Profile verfügbar.

## Konfigurationsoptionen

Die für jedes Profil verfügbaren Einstellungen hängen vom Blueprint ab. Gängige Konfigurationsoptionen umfassen:

### Modellauswahl

Wählen Sie, welches Sprachmodell der Agent verwendet. Die Optionen hängen davon ab, welche Modelle über Ihre LiteLLM-Konfiguration verfügbar sind.

### Temperatur

Steuert die Kreativität der Antworten:

- Niedrigere Werte (0.0-0.3): Fokussiertere, deterministische Antworten
- Höhere Werte (0.7-1.0): Kreativere, vielfältigere Antworten

### Wissensdatenbank

Wählen Sie für RAG-fähige Agents aus, welche Dokumentensammlungen der Agent durchsuchen kann.

### System-Prompt

Einige Agents ermöglichen die Anpassung des System-Prompts, um Verhalten und Persönlichkeit anzupassen.

## Berechtigungen

Der Zugriff auf Profile folgt dem Berechtigungssystem der Plattform:

- **Blueprint-Zugriff** (`aihub.admin.agent.{blueprint}.*`): Profile für einen spezifischen Blueprint verwalten
- **Profil-Zugriff** (`aihub.user.agent.{blueprint}.{profile_id}`): Ein spezifisches Profil verwenden
- **Wildcard-Zugriff** (`aihub.user.agent.*.>`): Zugriff auf alle Agents (typischerweise für Administratoren)

Siehe den Abschnitt [Zugriffsverwaltung](../../11_access_management/) für Details zur Konfiguration von Berechtigungen.

## Best Practices

### Namenskonventionen

- Verwenden Sie beschreibende Profilnamen, die den Zweck angeben („HR-Richtlinien-Assistent" statt „RAG Agent 1")
- Halten Sie Agent-IDs kurz, aber aussagekräftig (`hr_policy`, `legal_faq`)
- Fügen Sie die Zielgruppe in Beschreibungen ein („Für Mitarbeiter mit HR-Fragen")

### Konfigurationsstrategie

- Beginnen Sie mit konservativen Einstellungen (niedrigere Temperatur, kleinere Kontextfenster)
- Testen Sie mit repräsentativen Fragen, bevor Sie breit deployen
- Erstellen Sie separate Profile für verschiedene Anwendungsfälle anstelle eines generischen Profils

### Lifecycle-Management

- Überprüfen Sie die Profilnutzung regelmäßig anhand von Audit-Logs
- Stilllegen Sie ungenutzte Profile, um Verwirrung zu reduzieren
- Dokumentieren Sie Konfigurationsentscheidungen zur Wissensweitergabe im Team
```
