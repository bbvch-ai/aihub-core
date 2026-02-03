---
title: Internationalisierung
source_sha: e014188ae4ab25ca72820d07232aa4eeafc2f082eb0500fae163794cd1e3fc40
---

# Internationalisierung

Die Plattform unterstützt die vier Landessprachen der Schweiz: Deutsch, Englisch, Französisch und Italienisch. Benutzer
können die gesamte Oberfläche in ihrer bevorzugten Sprache nutzen.

## Sprachunterstützung

Deutsch dient als Standardsprache, doch alle vier Sprachen funktionieren identisch. Die Benutzeroberfläche,
Fehlermeldungen, Hilfetexte und Navigation sind alle übersetzt.

Alle benutzernahen Texte sind übersetzt – Formularvalidierung, Dialoge, Benachrichtigungen, Fehlermeldungen,
Hilfedokumentation und Anweisungen. Benutzer sehen keine unübersetzten Elemente oder gemischte Sprachen.

Dynamisch generierte Inhalte berücksichtigen ebenfalls die Sprachpräferenzen. Dienstleistungsbeschreibungen,
Agentennamen und Bezeichnungen von Wissens-Namespaces passen sich der gewählten Sprache an.

Benutzer wählen ihre Sprache während der Authentifizierung oder in den Profileinstellungen. Die Auswahl bleibt über
Sitzungen hinweg bestehen.

## Sprachauswahl und -wechsel

Benutzer konfigurieren ihre Sprache in ihrem Profil. Dies wird zur Standardsprache für alle Sitzungen und Geräte.

Benutzer können die Sprache temporär für eine bestimmte Sitzung wechseln. Dies unterstützt mehrsprachige Benutzer, die
für verschiedene Aufgaben unterschiedliche Sprachen bevorzugen.

Sprachänderungen werden sofort ohne Neuladen der Seite angewendet. Alle Texte werden sofort aktualisiert.

URLs enthalten keine Sprachcodes. Geteilte Links zeigen Inhalte in der bevorzugten Sprache des Empfängers an, nicht in
der des Absenders.

## Übersetzungsqualität

Die Plattform verwendet eine konsistente Terminologie über alle Sprachen hinweg. Gängige Begriffe wie „Agent“, „Thread“,
„Namespace“ und „Prozess“ verwenden in der gesamten Benutzeroberfläche dieselben Übersetzungen.

Spezialisierte Terminologie für technische KI-Konzepte und Schweizer Regulierungsterminologie erhält für jede Sprache
angemessene Übersetzungen.

Fehlt eine Übersetzung in der gewählten Sprache, greift die Plattform auf Deutsch zurück.

## Umgang mit lokalisierten Inhalten

Benutzerdefinierte Ressourcen können Übersetzungen für alle unterstützten Sprachen enthalten. Administratoren können
einen Wissens-Namespace-Namen und eine Beschreibung in Deutsch, Englisch, Französisch und Italienisch bereitstellen.

Das System kann die Dokumentsprache für die Verarbeitung und das Wissensmanagement automatisch erkennen. Dies ermöglicht
sprachspezifische Suchoptimierung und -abruf.

Zahlen, Daten, Zeiten und Währungen werden gemäß den regionalen Konventionen formatiert. Deutsche Benutzer sehen Daten
als „31.12.2024“, während englische Benutzer „12/31/2024“ sehen.

Die Suchfunktionalität verwendet sprachspezifische Tokenisierung und Stemming. Deutsche Suchen verwenden deutsche
linguistische Regeln, französische Suchen verwenden französische Regeln.

## Benutzerdefinierte Übersetzungen

Organisationen können benutzerdefinierte Übersetzungen für organisationsspezifische Begriffe wie interne Produktnamen,
benutzerdefinierte Rollen oder spezialisierte Prozesstypen hinzufügen. Administratoren können Übersetzungen über die
administrative Oberfläche der Plattform ändern.

## Barrierefreiheit und Internationalisierung

Bildschirmleser-Benutzer in allen Sprachen erhalten Beschreibungen in natürlicher Sprache anstelle von rein englischen
Alternativen.

Verschiedene Sprachen verwenden unterschiedliche Textlängen. Deutsche Übersetzungen sind oft länger als englische. Die
Benutzeroberfläche berücksichtigt diese Erweiterung, ohne das Layout zu beeinträchtigen.

Die Übersetzungsarchitektur kann bei Bedarf auf Sprachen mit Rechts-nach-Links-Schrift erweitert werden, obwohl die
derzeit unterstützten Sprachen alle Links-nach-Rechts-Text verwenden.

Barrierefreiheitskonventionen variieren je nach Region. Die Plattform kann Funktionen anpassen, um den Erwartungen der
Benutzer in verschiedenen Sprachgemeinschaften gerecht zu werden.

## Schweizer Organisationen

Schweizer Institutionen des öffentlichen Sektors müssen oft Dienstleistungen in mehreren Landessprachen anbieten. Die
Unterstützung von vier Sprachen durch die Plattform hilft, diese Anforderungen ohne kundenspezifische Entwicklung zu
erfüllen.

Organisationen, die in verschiedenen Schweizer Sprachregionen tätig sind, können eine einzige Plattforminstanz
bereitstellen. Benutzer in jeder Region sehen die Benutzeroberfläche in ihrer bevorzugten Sprache.

Schulungsmaterialien und Dokumentationen können in den Muttersprachen der Benutzer bereitgestellt werden.

Alle vier Sprachen funktionieren identisch. Keine Sprachgemeinschaft erlebt eine beeinträchtigte Nutzung.

Die Übersetzungsarchitektur ermöglicht es Organisationen, bei Bedarf weitere Sprachen hinzuzufügen – regionale Dialekte,
Sprachen von Einwanderergemeinschaften oder Sprachen internationaler Niederlassungen.
