---
title: Internationalisierung
source_sha: "6764df3224740726182ee7c89c934cddd89fab9522a3d15f0b47bcc9e37e33f7"
---

# Internationalisierung

Die Plattform unterstützt die vier Landessprachen der Schweiz: Deutsch, Englisch, Französisch und Italienisch. Benutzer können die Benutzeroberfläche durchgängig in ihrer bevorzugten Sprache verwenden.

## Sprachunterstützung

Deutsch dient als Standardsprache, aber alle vier Sprachen funktionieren identisch. Die Benutzeroberfläche, Fehlermeldungen, Hilfetexte und Navigation enthalten alle Übersetzungen.

Alle benutzernahen Texte sind übersetzt – Formularvalidierung, Dialoge, Benachrichtigungen, Fehlermeldungen, Hilfedokumentation und Anweisungen. Benutzer sehen keine unübersetzten Elemente oder gemischte Sprachen.

Dynamisch generierte Inhalte berücksichtigen ebenfalls die Sprachpräferenzen. Servicebeschreibungen, Agent-Namen und Knowledge-Namespace-Labels passen sich der ausgewählten Sprache an.

Benutzer wählen ihre Sprache während der Authentifizierung oder in den Profileinstellungen. Die Auswahl bleibt über Sitzungen hinweg bestehen.

## Sprachauswahl und -wechsel

Benutzer konfigurieren ihre Sprache in ihrem Profil. Dies wird zur Standardeinstellung für alle Sitzungen über Geräte hinweg.

Benutzer können die Sprache temporär für eine bestimmte Sitzung wechseln. Dies unterstützt mehrsprachige Benutzer, die für verschiedene Aufgaben unterschiedliche Sprachen bevorzugen.

Sprachänderungen werden sofort angewendet, ohne dass die Seite neu geladen werden muss. Alle Texte aktualisieren sich sofort.

URLs enthalten keine Sprachcodes. Geteilte Links zeigen Inhalte in der bevorzugten Sprache des Empfängers an, nicht in der des Absenders.

## Übersetzungsqualität

Die Plattform gewährleistet eine konsistente Terminologie über alle Sprachen hinweg. Gängige Begriffe wie „Agent“, „Thread“, „Namespace“ und „Prozess“ verwenden durchgängig dieselben Übersetzungen in der gesamten Benutzeroberfläche.

Spezialisierte Terminologie für technische KI-Konzepte und Schweizer Regulierungsvorschriften erhält für jede Sprache passende Übersetzungen.

Falls eine Übersetzung in der ausgewählten Sprache fehlt, greift die Plattform auf Deutsch zurück.

## Umgang mit lokalisiertem Inhalt

Benutzererstellte Ressourcen können Übersetzungen für alle unterstützten Sprachen enthalten. Administratoren können einen Knowledge-Namespace-Namen und eine Beschreibung in Deutsch, Englisch, Französisch und Italienisch bereitstellen.

Das System kann die Dokumentsprache für die Verarbeitung und das Wissensmanagement automatisch erkennen. Dies ermöglicht sprachspezifische Suchoptimierung und Abrufe.

Zahlen, Daten, Uhrzeiten und Währungen werden gemäß den regionalen Konventionen formatiert. Deutsche Benutzer sehen Daten als „31.12.2024“, während englische Benutzer „12/31/2024“ sehen.

Die Suchfunktion verwendet sprachspezifische Tokenisierung und Stemming. Deutsche Suchen verwenden deutsche linguistische Regeln, französische Suchen verwenden französische Regeln.

## Benutzerdefinierte Übersetzungen

Organisationen können benutzerdefinierte Übersetzungen für organisationsspezifische Begriffe wie interne Produktnamen, benutzerdefinierte Rollen oder spezialisierte Prozesstypen hinzufügen. Administratoren können Übersetzungen über die administrative Benutzeroberfläche der Plattform ändern.

## Barrierefreiheit und Internationalisierung

Bildschirmleser-Benutzer in allen Sprachen erhalten Beschreibungen in natürlicher Sprache anstelle von rein englischen Alternativen.

Verschiedene Sprachen verwenden unterschiedliche Textlängen. Deutsche Übersetzungen sind oft länger als englische. Die Benutzeroberfläche berücksichtigt diese Erweiterung, ohne das Layout zu beeinträchtigen.

Die Übersetzungsarchitektur kann bei Bedarf auf Sprachen mit Rechts-nach-links-Schreibweise erweitert werden, obwohl die derzeit unterstützten Sprachen alle Links-nach-rechts-Text verwenden.

Barrierefreiheitskonventionen variieren je nach Region. Die Plattform kann Funktionen anpassen, um den Benutzererwartungen in verschiedenen Sprachgemeinschaften gerecht zu werden.

## Schweizer Organisationen

Schweizer Institutionen des öffentlichen Sektors müssen oft Dienstleistungen in mehreren Landessprachen anbieten. Die Unterstützung von vier Sprachen durch die Plattform hilft, diese Anforderungen ohne kundenspezifische Entwicklung zu erfüllen.

Organisationen, die in verschiedenen Schweizer Sprachregionen tätig sind, können eine einzige Plattform-Instanz deployen. Benutzer in jeder Region sehen die Benutzeroberfläche in ihrer bevorzugten Sprache.

Schulungsmaterialien und Dokumentationen können in den Muttersprachen der Benutzer bereitgestellt werden.

Alle vier Sprachen funktionieren identisch. Keine Sprachgemeinschaft erlebt eine beeinträchtigte Erfahrung.

Die Übersetzungsarchitektur ermöglicht es Organisationen, bei Bedarf weitere Sprachen hinzuzufügen – regionale Dialekte, Sprachen von Einwanderergemeinschaften oder Sprachen internationaler Niederlassungen.
