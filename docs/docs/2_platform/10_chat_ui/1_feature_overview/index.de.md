```yaml
---
title: Feature-Übersicht
source_sha: "3d67e431fde8a1b6030847e47c37a8fec1a28365e6ce6a8e91239323268f92e4"
---
```

# Feature-Übersicht

Durch die Integration von Open WebUI bietet der Swiss AI Hub einen umfassenden Funktionsumfang. Dieser Abschnitt
dokumentiert die wichtigsten Funktionen, die über die Chat-Oberfläche verfügbar sind.

## Kern-Chat-Funktionen

Nachrichten werden in Echtzeit gestreamt, während die KI Antworten generiert. Benutzer können mit dem Lesen beginnen,
bevor die Generierung abgeschlossen ist, anstatt auf vollständige Antworten zu warten.

Die Oberfläche behält den Konversationskontext über mehrere Runden hinweg bei. Benutzer können Folgefragen stellen oder
Klarstellungen anfordern, ohne den Kontext neu herstellen zu müssen.

Benutzer können frühere Nachrichten bearbeiten, um Abfragen zu verfeinern, Nachrichten löschen, um irrelevante Inhalte
zu entfernen, oder Antworten neu generieren, um alternative Ausgaben zu erkunden.

Die Oberfläche ermöglicht die Kategorisierung von Konversationen durch Tags, eine durchsuchbare Historie und
Archivierung. Benutzer können organisierte Bibliotheken von Interaktionen pflegen, frühere Konversationen finden und
fortsetzen. Konversationen können gelöscht, mit anderen geteilt oder geklont werden, um sich in verschiedene Richtungen
aufzuteilen.

Volle Markdown-Wiedergabe ermöglicht Rich-Text-Formatierung sowohl in Benutzernachrichten als auch in KI-Antworten –
Überschriften, Listen, Tabellen, Code-Blöcke mit Syntaxhervorhebung. LaTeX-Unterstützung ermöglicht mathematische
Notation für technische und wissenschaftliche Anwendungen.

## Multimodale Interaktion

Benutzer können Nachrichten diktieren, anstatt sie einzugeben. Unterstützte Sprachen sind Englisch, Deutsch und
Schweizerdeutsch.

KI-Antworten können als Sprache wiedergegeben werden, wodurch Barrierefreiheitsanforderungen unterstützt und der
audiobasierte Konsum ermöglicht wird. Dies kommt sehbehinderten Benutzern und Szenarien zugute, in denen der Audiokonsum
bevorzugt wird.

Benutzer können Dokumente direkt in Konversationen hochladen und Fragen zum Dokumenteninhalt stellen oder eine Analyse
anfordern. Die Oberfläche verarbeitet PDFs, Office-Dokumente und Textdateien.

Für KI-Modelle, die Sehfunktionen unterstützen, können Benutzer Bilder in Konversationen einfügen und Analysen,
Beschreibungen oder Verarbeitungen anfordern.

## Modellverwaltung

Benutzer können mit mehreren KI-Modellen innerhalb derselben Oberfläche interagieren und Modelle basierend auf
Funktionsanforderungen, Kostenüberlegungen oder Leistungsmerkmalen auswählen.

Fortgeschrittene Benutzer können Modellparameter anpassen – Temperatur zur Kreativitätskontrolle, Token-Limits für die
Antwortlänge, Präsenzstrafen zur Reduzierung von Wiederholungen.

Organisationen können ihre eigenen „Modelle“ mit benutzerdefinierten Systemprompts definieren, die zu Basismodellen
hinzugefügt werden, ähnlich wie GPTs in OpenAI. Alle Parameter können voreingestellt werden, Wissen durch RAG kann
bereitgestellt und benutzerdefinierte Tools für bestimmte Modelle erstellt werden. Benutzer wählen Voreinstellungen,
anstatt manuell zu konfigurieren.

## Retrieval-Augmented Generation

Organisationen können KI-Modellen Zugriff auf benutzerdefinierte Dokumentensammlungen, in Open WebUI als „Knowledge“
bezeichnet, ermöglichen. Die Oberfläche übernimmt den Dokumenten-Upload, die Verarbeitung und die
Retrieval-Konfiguration.

Wenn RAG-Funktionen aktiviert sind, integrieren KI-Antworten Informationen aus konfigurierten Wissensdatenbanken und
liefern Antworten, die auf dem Organisationswissen basieren und nicht auf generischen Trainingsdaten.

Die native Oberfläche zeigt Indikatoren an, wenn Antworten abgerufene Informationen enthalten. Die erweiterte
Quellenattribution des Swiss AI Hub erweitert diese Funktionen, wie im Abschnitt zur Quellenattribution dokumentiert.

Administratoren können Dokumentensammlungen verwalten und Abrufparameter über integrierte Verwaltungsoberflächen
konfigurieren.

## Kollaboration und Freigabe

Benutzer können Konversationen mit Kollegen teilen, wodurch eine kollaborative KI-Interaktion ermöglicht wird. Geteilte
Konversationen behalten den vollständigen Kontext bei, sodass Empfänger den Verlauf überprüfen und Konversationen
fortsetzen können.

Benutzer können KI-Antworten mit Feedback versehen – Antworten als hilfreich oder problematisch markieren,
Korrekturhinweise geben oder kontextbezogene Notizen hinzufügen.

Bei Deployments, die Community-Interaktion ermöglichen, können Benutzer an Leaderboards teilnehmen, die eine produktive
Nutzung anerkennen, effektive Prompts oder Interaktionsmuster teilen und von erfolgreichen Anwendungen der Kollegen
lernen.

Mehrere Benutzer können in gemeinsamen Arbeitsbereichsumgebungen arbeiten, auf gemeinsame Konversationshistorien,
geteilte Wissensdatenbanken und kollaborative Interaktionen zugreifen, die teambasierte Arbeitsmuster unterstützen.

## Administration und Sicherheit

Administratoren definieren Benutzerrollen mit granularen Berechtigungen, die den Zugriff auf bestimmte Modelle,
Funktionen oder administrative Aufgaben steuern.

Administrative Oberflächen bieten Funktionen zur Benutzerbereitstellung, Authentifizierungskonfiguration und zum Entzug
von Zugriffsrechten. Die Integration mit Unternehmensauthentifizierungssystemen – OAuth, LDAP – ermöglicht eine
zentralisierte Benutzerverwaltung.

Für den programmatischen Zugriff können Administratoren API-Schlüssel generieren und verwalten, die externen Systemen
die Interaktion mit Chat-Funktionen ermöglichen. Die Berechtigungen von API-Schlüsseln können auf bestimmte Modelle oder
Operationen beschränkt werden.

Umfassende Protokollierung erfasst Benutzeraktivitäten, Modellinteraktionen und administrative Operationen und erstellt
Audit-Trails, die Compliance-Anforderungen und die Sicherheitsüberwachung unterstützen.

### Administratorzugriff auf Benutzerinhalte

Administrative Rechte umfassen nicht das Lesen von Inhalten anderer Personen. Standardmäßig sieht ein Chat-Administrator
nur die von ihm selbst hochgeladenen Dateien, und niemand – einschließlich Administratoren – kann Konversationen anderer
Benutzer exportieren. Dies gilt über Mandanten hinweg: Die Administration ist plattformweit, aber die Sichtbarkeit von
Uploads und Chats ist es nicht.

Deployments, die eine administrative Aufsicht für Support- oder Compliance-Workflows benötigen, können dies aktivieren,
indem sie `OPENWEBUI_BYPASS_ADMIN_ACCESS_CONTROL` (Dateien, plus Workspace-Modelle, Knowledge, Prompts und Tools) und
`OPENWEBUI_ENABLE_ADMIN_EXPORT` (Chat-Export) auf `true` setzen. Beide sind standardmäßig `false`.

Beachten Sie, dass die Chat-Administratorrolle von den Mandantenrollen der Plattform getrennt ist. Sie wird nur durch
die Realm-Rolle `AIHubSysAdmin` gewährt; ein Mandantenadministrator meldet sich hier als gewöhnlicher Benutzer an und
konnte niemals die Dateien oder Chats anderer Benutzer sehen. Siehe
[ADR: OpenWebUI-Admins auf eigene Dateien und Chats beschränken](/arc42/decisions/2026_09_07_openwebui_admin_scoped_to_own_data.md).

## Benutzererfahrung

Die Oberfläche passt sich an verschiedene Bildschirmgrößen und Geräte an – Desktop, Tablet, Mobile – und bewahrt
Funktionalität und Benutzerfreundlichkeit über alle Formfaktoren hinweg. Benutzer können Konversationen auf dem Desktop
beginnen und nahtlos auf Mobilgeräten fortsetzen.

Die Oberfläche kann als Progressive Web App (PWA) installiert werden, wodurch native, anwendungsähnliche Erlebnisse
einschließlich Offline-Funktionalität, Push-Benachrichtigungen und Präsenz auf dem Startbildschirm ermöglicht werden,
ohne eine App Store-Verteilung zu erfordern.

Benutzer können aus mehreren visuellen Themen wählen – Light Mode, Dark Mode, Optionen mit hohem Kontrast – um das
Erscheinungsbild der Oberfläche an persönliche Vorlieben und die Umgebungsbeleuchtung anzupassen.

## Erweiterte Funktionen

Für unterstützte Modelle und Konfigurationen kann die Oberfläche Code-Snippets ausführen, was interaktive
Programmierhilfe, rechnerische Problemlösung und Algorithmus-Prototyping innerhalb von Konversationskontexten
ermöglicht.

Dieselbe Sandbox ermöglicht es Modellen, Dateien zu produzieren – Berichte, Tabellenkalkulationen, Präsentationen,
Diagramme, Audio und Video –, die das Modell dann im Dateibetrachter des Benutzers öffnet. Dies erfordert keinen Code
vom Benutzer; siehe [Dateigenerierung](../13_file_generation/) für die unterstützten Formate und das empfohlene Modell.

Mermaid-Diagramm-Unterstützung ermöglicht KI-generierte Visualisierungen – Flussdiagramme, Sequenzdiagramme,
Zustandsautomaten – die direkt in Konversationen gerendert werden. Dies unterstützt Systemdesign, Prozessdokumentation
und visuelle Erklärungen.

Das Erweiterbarkeits-Framework ermöglicht die Integration von benutzerdefinierten Verarbeitungspipelines, Tools und
Funktionen. Organisationen können die Chat-Funktionalität mit geschäftsspezifischen Operationen erweitern, ohne den
Kern-Interface-Code zu ändern.

Bei entsprechender Konfiguration können KI-Modelle auf Websuchfunktionen zugreifen, um aktuelle Informationen über die
Trainingsdaten hinaus einzubeziehen. Dies unterstützt Abfragen, die aktuelle Informationen oder eine Überprüfung anhand
aktueller Quellen erfordern.

## Was dies bietet

Organisationen, die den Swiss AI Hub deployen, erhalten diese Open WebUI-Funktionen sofort, ohne Entwicklungsaufwand.
Wenn die Open WebUI-Community neue Funktionen hinzufügt, profitiert der Swiss AI Hub durch standardmäßige Update-Zyklen.

Organisationen erhalten ausgereifte Funktionalität, die von globalen Communities entwickelt wurde, erweitert um
unternehmensspezifische Funktionen wie Quellenattribution und Ausführungsverfolgung.

```
```
