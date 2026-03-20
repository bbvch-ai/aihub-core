---
title: Funktionsübersicht
source_sha: 372f92552bca6a8de6b631b7437cd9b9cb5943fdf219709ad021529d1683074a
---

# Funktionsübersicht

Durch die Integration von Open WebUI bietet der Swiss AI Hub einen umfassenden Funktionsumfang. Dieser Abschnitt
dokumentiert die wichtigsten Funktionen, die über die Chat-Oberfläche verfügbar sind.

## Kernfunktionen des Chats

Nachrichten werden in Echtzeit gestreamt, während die KI Antworten generiert. Benutzer können mit dem Lesen beginnen,
bevor die Generierung abgeschlossen ist, anstatt auf vollständige Antworten zu warten.

Die Oberfläche behält den Konversationskontext über mehrere Runden hinweg bei. Benutzer können Anschlussfragen stellen
oder um Klärungen bitten, ohne den Kontext neu herstellen zu müssen.

Benutzer können frühere Nachrichten bearbeiten, um Anfragen zu verfeinern, Nachrichten löschen, um irrelevante Inhalte
zu entfernen, oder Antworten neu generieren, um alternative Ausgaben zu erkunden.

Die Oberfläche bietet eine Konversationskategorisierung durch Tags, eine durchsuchbare Historie und
Archivierungsfunktionen. Benutzer können organisierte Bibliotheken ihrer Interaktionen pflegen, frühere Konversationen
finden und fortsetzen. Konversationen können gelöscht, mit anderen geteilt oder geklont werden, um sich in verschiedene
Richtungen zu verzweigen.

Die vollständige Markdown-Darstellung ermöglicht eine umfassende Textformatierung sowohl in Benutzernachrichten als auch
in KI-Antworten – Überschriften, Listen, Tabellen, Code-Blöcke mit Syntaxhervorhebung. Die LaTeX-Unterstützung
ermöglicht mathematische Notation für technische und wissenschaftliche Anwendungen.

## Multimodale Interaktion

Benutzer können Nachrichten diktieren, anstatt sie zu tippen. Unterstützte Sprachen sind Englisch, Deutsch und
Schweizerdeutsch.

KI-Antworten können als Sprache wiedergegeben werden, wodurch Barrierefreiheitsanforderungen unterstützt und der
audiobasierte Konsum ermöglicht wird. Dies kommt sehbehinderten Benutzern und Szenarien zugute, in denen der
Audio-Konsum bevorzugt wird.

Benutzer können Dokumente direkt in Konversationen hochladen, Fragen zum Dokumentinhalt stellen oder eine Analyse
anfordern. Die Oberfläche verarbeitet PDFs, Office-Dokumente und Textdateien.

Für KI-Modelle, die Vision-Fähigkeiten unterstützen, können Benutzer Bilder in Konversationen einfügen, um Analyse,
Beschreibung oder Verarbeitung anzufordern.

## Modellverwaltung

Benutzer können mit mehreren KI-Modellen innerhalb derselben Oberfläche interagieren und Modelle basierend auf
Fähigkeitsanforderungen, Kostenüberlegungen oder Leistungsmerkmalen auswählen.

Fortgeschrittene Benutzer können Modellparameter anpassen – Temperatur zur Kontrolle der Kreativität, Token-Limits für
die Antwortlänge, Anwesenheitsstrafen zur Reduzierung von Wiederholungen.

Organisationen können eigene „Modelle“ mit benutzerdefinierten System-Prompts definieren, die zu Basismodellen
hinzugefügt werden, ähnlich wie GPTs in OpenAI. Alle Parameter können voreingestellt werden, Wissen über RAG kann
bereitgestellt und benutzerdefinierte Tools für spezifische Modelle erstellt werden. Benutzer wählen Voreinstellungen,
anstatt manuell zu konfigurieren.

## Retrieval-Augmented Generation (RAG)

Organisationen können KI-Modellen Zugang zu benutzerdefinierten Dokumentensammlungen gewähren, die in Open WebUI als
„Wissen“ bezeichnet werden. Die Oberfläche übernimmt den Dokumentenupload, die Verarbeitung und die
Retrieval-Konfiguration.

Wenn RAG-Funktionen aktiviert sind, integrieren KI-Antworten Informationen aus konfigurierten Wissensbasen und liefern
Antworten, die auf organisatorischem Wissen und nicht auf generischen Trainingsdaten basieren.

Die native Oberfläche bietet Indikatoren, wenn Antworten abgerufene Informationen enthalten. Die erweiterte
Quellenattribution des Swiss AI Hub erweitert diese Funktionen, wie im Abschnitt Quellenattribution dokumentiert.

Administratoren können Dokumentensammlungen verwalten und Retrieval-Parameter über integrierte Verwaltungsoberflächen
konfigurieren.

## Zusammenarbeit und Teilen

Benutzer können Konversationen mit Kollegen teilen, was eine kollaborative KI-Interaktion ermöglicht. Geteilte
Konversationen behalten den vollständigen Kontext bei, sodass Empfänger die Historie überprüfen und Konversationen
fortsetzen können.

Benutzer können KI-Antworten mit Feedback versehen – Antworten als hilfreich oder problematisch markieren,
Korrekturhinweise geben oder kontextbezogene Notizen hinzufügen.

Bei Deployments, die Community-Interaktion ermöglichen, können Benutzer an Bestenlisten teilnehmen, die eine produktive
Nutzung anerkennen, effektive Prompts oder Interaktionsmuster teilen und von erfolgreichen Anwendungen der Kollegen
lernen.

Mehrere Benutzer können in geteilten Arbeitsbereichen arbeiten, auf gemeinsame Konversationshistorien, geteilte
Wissensbasen und kollaborative Interaktionen zugreifen, die teambasierte Arbeitsmuster unterstützen.

## Administration und Sicherheit

Administratoren definieren Benutzerrollen mit granularen Berechtigungen, die den Zugriff auf bestimmte Modelle,
Funktionen oder administrative Aufgaben steuern.

Administrative Oberflächen bieten Funktionen zur Benutzerbereitstellung, Authentifizierungskonfiguration und
Zugriffsaufhebung. Die Integration mit Unternehmens-Authentifizierungssystemen – OAuth, LDAP – ermöglicht eine zentrale
Benutzerverwaltung.

Für den programmatischen Zugriff können Administratoren API-Schlüssel generieren und verwalten, die externen Systemen
die Interaktion mit Chat-Funktionen ermöglichen. API-Schlüsselberechtigungen können auf bestimmte Modelle oder
Operationen zugeschnitten werden.

Eine umfassende Protokollierung erfasst Benutzeraktivitäten, Modellinteraktionen und administrative Vorgänge und
erstellt Audit-Trails, die Compliance-Anforderungen und Sicherheitsüberwachung unterstützen.

## Benutzererfahrung

Die Oberfläche passt sich an verschiedene Bildschirmgrößen und Geräte an – Desktop, Tablet, Mobilgerät – und bewahrt
Funktionalität und Benutzerfreundlichkeit über verschiedene Formfaktoren hinweg. Benutzer können Konversationen auf dem
Desktop beginnen und nahtlos auf Mobilgeräten fortsetzen.

Die Oberfläche kann als Progressive Web App installiert werden, die native Anwendungsähnliche Erlebnisse bietet,
einschließlich Offline-Fähigkeit, Push-Benachrichtigungen und Präsenz auf dem Startbildschirm, ohne eine Verteilung über
App-Stores zu erfordern.

Benutzer können aus mehreren visuellen Themes wählen – Hellmodus, Dunkelmodus, Optionen mit hohem Kontrast – um das
Erscheinungsbild der Oberfläche an persönliche Vorlieben und die Umgebungsbeleuchtung anzupassen.

## Erweiterte Funktionen

Für unterstützte Modelle und Konfigurationen kann die Oberfläche Code-Snippets ausführen, was interaktive
Programmierhilfe, rechnerische Problemlösung und Algorithmus-Prototyping innerhalb von Konversationskontexten
ermöglicht.

Die Unterstützung für Mermaid-Diagramme ermöglicht KI-generierte Visualisierungen – Flussdiagramme, Sequenzdiagramme,
Zustandsautomaten – die direkt in Konversationen gerendert werden. Dies unterstützt Systemdesign, Prozessdokumentation
und visuelle Erklärungen.

Das Erweiterbarkeits-Framework ermöglicht die Integration von benutzerdefinierten Verarbeitungspipelines, Tools und
Funktionen. Organisationen können die Chat-Funktionalität mit geschäftsspezifischen Operationen erweitern, ohne den
Kern-Schnittstellencode zu ändern.

Bei Konfiguration können KI-Modelle auf Web-Suchfunktionen zugreifen, um aktuelle Informationen über die Trainingsdaten
hinaus zu integrieren. Dies unterstützt Abfragen, die aktuelle Informationen oder eine Überprüfung anhand aktueller
Quellen erfordern.

## Was dies bietet

Organisationen, die den Swiss AI Hub deployen, erhalten diese Open WebUI-Funktionen sofort und ohne Entwicklungsaufwand.
Wenn die Open WebUI-Community neue Funktionen hinzufügt, profitiert der Swiss AI Hub durch standardmäßige Update-Zyklen.

Organisationen erhalten ausgereifte Funktionalität, die von globalen Communities entwickelt wurde, erweitert um
unternehmensspezifische Funktionen wie Quellenattribution und Ausführungsverfolgung.
