---
title: Funktionsübersicht
source_sha: 7dc33a8c6a266274d9d5279f19cde6076774eac20a3a0a47dfcdc86d2034dbb4
---

# Funktionsübersicht

Durch die Integration von Open WebUI bietet der Swiss AI Hub einen umfassenden Funktionsumfang. Dieser Abschnitt
dokumentiert die wichtigsten Funktionen, die über die Chat-Oberfläche verfügbar sind.

## Kern-Chat-Funktionen

Nachrichten werden in Echtzeit gestreamt, während die KI Antworten generiert. Benutzer können mit dem Lesen beginnen,
bevor die Generierung abgeschlossen ist, anstatt auf vollständige Antworten zu warten.

Die Oberfläche behält den Konversationskontext über mehrere Runden hinweg bei. Benutzer können Anschlussfragen stellen
oder um Klärungen bitten, ohne den Kontext neu herstellen zu müssen.

Benutzer können frühere Nachrichten bearbeiten, um Abfragen zu verfeinern, Nachrichten löschen, um irrelevante Inhalte
zu entfernen, oder Antworten neu generieren, um alternative Ausgaben zu erkunden.

Die Oberfläche bietet Konversationskategorisierung durch Tags, durchsuchbare Historie und Archivierung. Benutzer können
organisierte Bibliotheken von Interaktionen pflegen, frühere Konversationen finden und fortsetzen. Konversationen können
gelöscht, mit anderen geteilt oder geklont werden, um sich in verschiedene Richtungen aufzuteilen.

Die vollständige Markdown-Darstellung ermöglicht Rich-Text-Formatierung sowohl in Benutzernachrichten als auch in
KI-Antworten – Überschriften, Listen, Tabellen, Codeblöcke mit Syntaxhervorhebung. LaTeX-Unterstützung ermöglicht
mathematische Notation für technische und wissenschaftliche Anwendungen.

## Multimodale Interaktion

Benutzer können Nachrichten diktieren, anstatt zu tippen. Unterstützte Sprachen sind Englisch, Deutsch und
Schweizerdeutsch.

KI-Antworten können als Sprache ausgegeben werden, was Barrierefreiheitsanforderungen unterstützt und den audiobasierten
Konsum ermöglicht. Dies kommt sehbehinderten Benutzern und Szenarien zugute, in denen der Audiokonsum bevorzugt wird.

Benutzer können Dokumente direkt in Konversationen hochladen, Fragen zum Dokumenteninhalt stellen oder eine Analyse
anfordern. Die Oberfläche verarbeitet PDFs, Office-Dokumente und Textdateien.

Für KI-Modelle, die Sehfunktionen unterstützen, können Benutzer Bilder in Konversationen einfügen, um Analyse,
Beschreibung oder Verarbeitung anzufordern.

## Modellverwaltung

Benutzer können innerhalb derselben Oberfläche mit mehreren KI-Modellen interagieren und Modelle basierend auf
Leistungsanforderungen, Kostenüberlegungen oder Leistungsmerkmalen auswählen.

Fortgeschrittene Benutzer können Modellparameter anpassen – Temperatur zur Steuerung der Kreativität, Token-Limits für
die Antwortlänge, Präsenzstrafen zur Reduzierung von Wiederholungen.

Organisationen können ihre eigenen „Modelle“ mit benutzerdefinierten System-Prompts definieren, die zu Basismodellen
hinzugefügt werden, ähnlich den GPTs in OpenAI. Alle Parameter können voreingestellt werden, Wissen durch RAG kann
bereitgestellt und benutzerdefinierte Tools für spezifische Modelle erstellt werden. Benutzer wählen Voreinstellungen,
anstatt manuell zu konfigurieren.

## Abfragegestützte Generierung

Organisationen können KI-Modellen Zugang zu benutzerdefinierten Dokumentensammlungen, in Open WebUI als „Wissen“
bezeichnet, ermöglichen. Die Oberfläche übernimmt den Dokumenten-Upload, die Verarbeitung und die Abfragekonfiguration.

Wenn RAG-Funktionen aktiviert sind, integrieren KI-Antworten Informationen aus konfigurierten Wissensbasen und liefern
Antworten, die auf organisationsspezifischem Wissen basieren, anstatt auf generischen Trainingsdaten.

Die native Oberfläche zeigt Indikatoren an, wenn Antworten abgerufene Informationen enthalten. Die verbesserte
Quellenattribution des Swiss AI Hub erweitert diese Funktionen, wie im Abschnitt zur Quellenattribution dokumentiert.

Administratoren können Dokumentensammlungen verwalten und Abfrageparameter über integrierte Verwaltungsoberflächen
konfigurieren.

## Zusammenarbeit und Freigabe

Benutzer können Konversationen mit Kollegen teilen, was eine kollaborative KI-Interaktion ermöglicht. Geteilte
Konversationen behalten den vollständigen Kontext bei, sodass Empfänger den Verlauf überprüfen und Konversationen
fortsetzen können.

Benutzer können KI-Antworten mit Feedback versehen – Antworten als hilfreich oder problematisch markieren,
Korrekturhinweise geben oder kontextbezogene Notizen hinzufügen.

Für Bereitstellungen, die Community-Interaktion ermöglichen, können Benutzer an Bestenlisten teilnehmen, die eine
produktive Nutzung anerkennen, effektive Prompts oder Interaktionsmuster teilen und von erfolgreichen Anwendungen der
Kollegen lernen.

Mehrere Benutzer können in gemeinsamen Arbeitsbereichsumgebungen arbeiten, auf gemeinsame Konversationsverläufe,
geteilte Wissensbasen und kollaborative Interaktionen zugreifen, die teambasierte Arbeitsmuster unterstützen.

## Administration und Sicherheit

Administratoren definieren Benutzerrollen mit granularen Berechtigungen, die den Zugriff auf bestimmte Modelle,
Funktionen oder administrative Aufgaben steuern.

Administrative Oberflächen bieten Funktionen zur Benutzerbereitstellung, Authentifizierungskonfiguration und
Zugriffsaufhebung. Die Integration mit unternehmenseigenen Authentifizierungssystemen – OAuth, LDAP – ermöglicht eine
zentralisierte Benutzerverwaltung.

Für den programmatischen Zugriff können Administratoren API-Schlüssel generieren und verwalten, die externen Systemen
die Interaktion mit Chat-Funktionen ermöglichen. API-Schlüsselberechtigungen können auf bestimmte Modelle oder
Operationen zugeschnitten werden.

Eine umfassende Protokollierung erfasst Benutzeraktivitäten, Modellinteraktionen und administrative Vorgänge und
erstellt Audit-Trails, die Compliance-Anforderungen und Sicherheitsüberwachung unterstützen.

## Benutzererfahrung

Die Oberfläche passt sich verschiedenen Bildschirmgrößen und Geräten an – Desktop, Tablet, Mobiltelefon – und behält die
Funktionalität und Benutzerfreundlichkeit über verschiedene Formfaktoren hinweg bei. Benutzer können Konversationen auf
dem Desktop beginnen und sie nahtlos auf dem Mobiltelefon fortsetzen.

Die Oberfläche kann als Progressive Web App installiert werden und bietet native anwendungsähnliche Erlebnisse,
einschließlich Offline-Fähigkeit, Push-Benachrichtigungen und Präsenz auf dem Startbildschirm, ohne eine
App-Store-Verteilung zu erfordern.

Benutzer können aus mehreren visuellen Themen wählen – Hellmodus, Dunkelmodus, Optionen mit hohem Kontrast – um das
Erscheinungsbild der Oberfläche an persönliche Vorlieben und die Umgebungsbeleuchtung anzupassen.

## Erweiterte Funktionen

Für unterstützte Modelle und Konfigurationen kann die Oberfläche Code-Snippets ausführen, was interaktive
Programmierunterstützung, rechnerische Problemlösung und Algorithmus-Prototyping innerhalb konversationeller Kontexte
ermöglicht.

Die Unterstützung von Mermaid-Diagrammen ermöglicht KI-generierte Visualisierungen – Flussdiagramme, Sequenzdiagramme,
Zustandsautomaten – die direkt in Konversationen gerendert werden. Dies unterstützt Systemdesign, Prozessdokumentation
und visuelle Erklärungen.

Das Erweiterbarkeits-Framework ermöglicht die Integration benutzerdefinierter Verarbeitungspipelines, Tools und
Funktionen. Organisationen können die Chat-Funktionalität mit geschäftsspezifischen Operationen erweitern, ohne den
Kerncode der Oberfläche ändern zu müssen.

Bei entsprechender Konfiguration können KI-Modelle auf Web-Suchfunktionen zugreifen, um aktuelle Informationen über die
Trainingsdaten hinaus zu integrieren. Dies unterstützt Abfragen, die aktuelle Informationen oder eine Überprüfung anhand
aktueller Quellen erfordern.

## Was dies bietet

Organisationen, die den Swiss AI Hub implementieren, erhalten diese Open WebUI-Funktionen sofort und ohne
Entwicklungsaufwand. Wenn die Open WebUI-Community neue Funktionen hinzufügt, profitiert der Swiss AI Hub durch
standardmäßige Update-Zyklen.

Organisationen erhalten ausgereifte Funktionen, die von globalen Communities entwickelt wurden, erweitert um
unternehmensspezifische Funktionen wie Quellenattribution und Ausführungsverfolgung.
