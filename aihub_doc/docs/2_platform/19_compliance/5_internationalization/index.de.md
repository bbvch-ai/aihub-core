---
title: Internationalisierung
index: 5
source_sha: "aca3074ef22182cbf9932595c062d423f6b3cd8019606d8444f5f7c030d3b9ff"
---

# Internationalisierung

Die Benutzeroberfläche der Swiss AI Hub Suite bietet umfassende Internationalisierungsunterstützung, die die sprachliche Vielfalt der Schweiz widerspiegelt. Diese Fähigkeit gewährleistet einen gleichberechtigten Zugang für alle Schweizer Sprachgemeinschaften und unterstützt den Einsatz der Plattform in mehrsprachigen Organisationen und öffentlichen Institutionen.

## Mehrsprachige Grundlage

Die Suite implementiert Internationalisierung als ein zentrales Architekturprinzip und nicht als nachträgliche Ergänzung. Dadurch wird sichergestellt, dass sich alle Oberflächenelemente, Nachrichten und Inhalte an die Sprachpräferenzen der Benutzer anpassen.

**Unterstützte Sprachen**: Die Suite bietet volle Unterstützung für die vier Landessprachen der Schweiz – Deutsch, Englisch, Französisch und Italienisch. Jedes Oberflächenelement, von Navigationsbezeichnungen über Fehlermeldungen bis hin zu Hilfetexten, enthält Übersetzungen in allen vier Sprachen. Deutsch dient als Standardsprache und spiegelt die primäre Entwicklungsregion wider, aber alle Sprachen erhalten die gleiche Behandlung in Bezug auf Funktionalität und Ausfeilung.

**Volle Abdeckung**: Die Internationalisierung geht über einfache Beschriftungen hinaus und umfasst alle benutzerseitigen Texte – Formularvalidierungsmeldungen, Bestätigungsdialoge, Erfolgsmeldungen, Fehlererklärungen, Hilfedokumentation und Anweisungstexte. Benutzer, die in ihrer bevorzugten Sprache arbeiten, stoßen auf keine unübersetzten Elemente oder Sprachinkonsistenzen.

**Dynamische Inhaltslokalisierung**: Neben statischem Interface-Text berücksichtigt dynamisch generierter Inhalt die Sprachpräferenzen. Dienstbeschreibungen, Agentennamen, Bezeichnungen für Knowledge Namespaces – jeder Inhalt, der Lokalisierung unterstützt, passt sich der Sprachauswahl des Benutzers an und schafft so eine vollständig lokalisierte Erfahrung.

**Die richtige Sprache von Anfang an**: Benutzer wählen ihre bevorzugte Sprache während der ersten Authentifizierung oder über die Profileinstellungen. Diese Auswahl bleibt über Sitzungen hinweg bestehen und stellt sicher, dass Benutzer die Oberfläche konsistent in ihrer gewählten Sprache erleben, ohne sie wiederholt auswählen zu müssen.

## Sprachauswahl und -wechsel

Die Suite bietet flexible Mechanismen zur Sprachauswahl, die die Benutzerkontrolle mit der betrieblichen Effizienz in Einklang bringen.

**Profilbasierte Auswahl**: Benutzer konfigurieren ihre Sprachpräferenz in ihrem Benutzerprofil. Diese Einstellung wird zur Standardeinstellung für alle Sitzungen und gewährleistet eine konsistente Spracherfahrung über Geräte und Anmeldesitzungen hinweg, ohne dass eine wiederholte Auswahl erforderlich ist.

**Sitzungsüberschreibung**: Benutzer können ihre im Profil festgelegte Sprachpräferenz für eine bestimmte Sitzung temporär über Bedienelemente der Benutzeroberfläche außer Kraft setzen. Diese Funktion unterstützt mehrsprachige Benutzer, die möglicherweise unterschiedliche Sprachen für verschiedene Aufgaben oder Kontexte bevorzugen.

**Sofortige Anwendung**: Sprachänderungen werden sofort in der gesamten Benutzeroberfläche angewendet, ohne dass ein Neuladen der Seite oder ein Logout erforderlich ist. Navigationselemente, Dienstbeschreibungen, Formularbeschriftungen und alle Oberflächentxte werden sofort aktualisiert, um die ausgewählte Sprache widerzuspiegeln.

**URL-Unabhängigkeit**: Die Suite verwaltet die Sprachauswahl unabhängig von der URL-Struktur. Benutzer können Links zu Ressourcen teilen, ohne dass Sprachcodes in den URLs eingebettet sind, wodurch sichergestellt wird, dass Empfänger Inhalte in ihrer bevorzugten Sprache sehen und nicht in der Sprache des Link-Teilers.

## Übersetzungsarchitektur

Die Suite implementiert eine hochentwickelte Übersetzungsarchitektur, die Wartbarkeit, Erweiterbarkeit und konsistente Terminologie über die gesamte Plattform hinweg gewährleistet.

**Schlüsselbasierte Übersetzung**: Alle benutzerseitigen Texte werden über Übersetzungsschlüssel und nicht über fest codierte Zeichenfolgen referenziert. Entwickler verweisen auf Schlüssel wie `agent.create.title` anstatt auf wörtlichen Text, wodurch sichergestellt wird, dass Übersetzungen ohne Codeänderungen angepasst oder erweitert werden können.

**YAML-basierte Übersetzungsdateien**: Übersetzungen werden in YAML-Dateien verwaltet, die nach Dienst und Sprache organisiert sind. Jeder Dienst pflegt seine eigenen Übersetzungsdateien für die vier unterstützten Sprachen, wodurch sichergestellt wird, dass die dienstspezifische Terminologie konsistent bleibt und unabhängige Übersetzungsaktualisierungen ermöglicht werden.

**Hierarchische Schlüsselstruktur**: Übersetzungsschlüssel folgen einer hierarchischen Struktur, die die Oberflächenorganisation widerspiegelt. Schlüssel wie `knowledge.namespace.create.label` organisieren Übersetzungen logisch, machen sie auffindbar und verhindern Namenskollisionen in der großen Codebasis.

**Fallback-Mechanismen**: Das Übersetzungssystem implementiert hochentwickelte Fallback-Mechanismen. Fehlt eine Übersetzung in der vom Benutzer gewählten Sprache, greift das System auf Deutsch (die Standardsprache) zurück. Fehlt selbst die deutsche Übersetzung, zeigt das System den Übersetzungsschlüssel selbst an, wodurch fehlende Übersetzungen während der Entwicklung und des Testens offensichtlich werden.

## Terminologiekonsistenz

Die Aufrechterhaltung einer konsistenten Terminologie über alle Sprachen hinweg ist entscheidend für das Benutzerverständnis und eine professionelle Präsentation.

**Gemeinsame Glossare**: Die Plattform pflegt gemeinsame Glossare, die Standardübersetzungen für gängige Begriffe definieren – „Agent“, „Thread“, „Namespace“, „Prozess“. Dienste verweisen auf diese gemeinsamen Übersetzungen, anstatt dienstspezifische Varianten zu erstellen, wodurch sichergestellt wird, dass Benutzer unabhängig vom verwendeten Dienst auf konsistente Terminologie stoßen.

**Domänenspezifische Begriffe**: Für spezialisierte Terminologie (technische KI-Konzepte, schweizerische regulatorische Begriffe, branchenspezifische Sprache) ermöglicht das Übersetzungssystem domänenspezifische Glossare, die kontextgerechte Übersetzungen bereitstellen und gleichzeitig die allgemeine Konsistenz wahren.

**Professionelle Übersetzung**: Anstatt sich ausschließlich auf maschinelle Übersetzung zu verlassen, sollten die Übersetzungen der Plattform einer professionellen Überprüfung durch Muttersprachler unterzogen werden, die sowohl mit der Ausgangssprache als auch mit technischen Konzepten vertraut sind. Dies stellt sicher, dass die Übersetzungen natürlich klingen und eine angemessene professionelle Terminologie verwenden.

**Kontinuierliche Verfeinerung**: Wenn Benutzer Feedback zu Übersetzungen geben, unterstützt die Plattform eine iterative Verfeinerung. Übersetzungsaktualisierungen werden unabhängig von Codeänderungen bereitgestellt, was eine schnelle Reaktion auf Feedback ohne vollständige Plattform-Releases ermöglicht.

## Lokalisierte Inhaltsbehandlung

Über die Schnittstellenübersetzung hinaus handhabt die Suite benutzergenerierte und systemgenerierte Inhalte auf lokalisierte Weise.

**Mehrsprachige Metadaten**: Vom Benutzer erstellte Ressourcen (Knowledge Namespaces, Agentenbeschreibungen, Prozessnamen) können Übersetzungen für alle unterstützten Sprachen enthalten. Administratoren, die einen Knowledge Namespace erstellen, können dessen Namen und Beschreibung auf Deutsch, Englisch, Französisch und Italienisch bereitstellen, um sicherzustellen, dass alle Benutzer diese Ressourcen in ihrer Sprache beschrieben sehen.

**Automatische Spracherkennung**: Für die Dokumentenverarbeitung und das Wissensmanagement kann das System die Dokumentsprache automatisch erkennen, was eine sprachspezifische Verarbeitung, Suchoptimierung und Retrieval-Anpassung ermöglicht.

**Lokalisierte Formatierung**: Zahlen, Daten, Uhrzeiten und Währungen werden gemäß den Gebietsschema-Konventionen formatiert. Deutsche Benutzer sehen Daten als „31.12.2024“, während englische Benutzer „12/31/2024“ sehen. Währungsbeträge, Prozentsätze und große Zahlen beachten die Formatierungsregeln des Gebietsschemas.

**Suchlokalisierung**: Die Suchfunktion berücksichtigt Sprachkontexte. Suchen auf Deutsch verwenden deutschspezifische Tokenisierung und Stemming, während französische Suchen französische linguistische Regeln anwenden. Dies stellt sicher, dass die Suchergebnisse über Sprachen hinweg relevant bleiben.

## Administrative Überlegungen

Plattformadministratoren profitieren von umfassenden Funktionen zur Internationalisierungsverwaltung.

**Übersetzungsmanagement-Oberfläche**: Administratoren mit entsprechenden Berechtigungen können Übersetzungen über dedizierte Verwaltungsoberflächen überprüfen und ändern, Terminologie aktualisieren oder benutzerdefinierte Übersetzungen für organisationsspezifische Begriffe hinzufügen, ohne YAML-Dateien direkt bearbeiten zu müssen.

**Überwachung der Übersetzungsabdeckung**: Administrative Dashboards können die Vollständigkeit der Übersetzungen über alle Sprachen hinweg anzeigen – sie identifizieren Oberflächenelemente, denen in bestimmten Sprachen Übersetzungen fehlen, und ermöglichen die systematische Vervollständigung der Übersetzungsabdeckung.

**Unterstützung benutzerdefinierter Terminologie**: Organisationen können das Übersetzungssystem mit benutzerdefinierten Begriffen erweitern, die spezifisch für ihren Kontext sind – interne Produktnamen, organisationsspezifische Rollen, benutzerdefinierte Prozesstypen. Diese benutzerdefinierten Übersetzungen integrieren sich nahtlos in die Plattformübersetzungen.

**Sprachnutzungsanalysen**: Die Plattform kann verfolgen, welche Sprachen Benutzer auswählen, was Entscheidungen über Prioritäten bei Übersetzungsinvestitionen informiert und Organisationen hilft, die sprachliche Zusammensetzung ihrer Benutzerbasis zu verstehen.

## Schnittstelle von Barrierefreiheit und Internationalisierung

Internationalisierung überschneidet sich in wichtigen Aspekten mit den Anforderungen an die Barrierefreiheit.

**Screenreader-Unterstützung**: Übersetzungen stellen sicher, dass Screenreader-Benutzer in allen Sprachen angemessene, natürlichsprachliche Beschreibungen von Oberflächenelementen erhalten, anstatt englischsprachige Alternativen, die in unzureichend lokalisierten Anwendungen üblich sind.

**Umgang mit Textlängenerweiterung**: Verschiedene Sprachen drücken dieselben Konzepte mit unterschiedlicher Textlänge aus. Deutsche Übersetzungen können erheblich länger sein als englische Äquivalente. Das Interface-Design berücksichtigt diese Textlängenerweiterung, ohne Layouts zu zerstören oder Inhalte unlesbar zu machen.

**Unterstützung von Fließrichtung**: Während die aktuell unterstützten Sprachen alle von links nach rechts verlaufen, kann die Übersetzungsarchitektur erweitert werden, um Sprachen mit rechts-nach-links-Fließrichtung zu unterstützen, sollten die Bereitstellungsanforderungen über die Landessprachen der Schweiz hinausgehen.

**Gebietsschemaspezifische Barrierefreiheit**: Barrierefreiheitskonventionen variieren je nach Gebietsschema. Die Plattform kann Barrierefreiheitsfunktionen an die Erwartungen der Benutzer in ihrer Sprachgemeinschaft anpassen.

## Geschäftswert für Schweizer Organisationen

Eine umfassende Internationalisierung liefert spezifischen Wert für Schweizer Organisationen und öffentliche Institutionen.

**Konformität im öffentlichen Sektor**: Schweizer Institutionen des öffentlichen Sektors haben oft regulatorische Anforderungen, Dienstleistungen in mehreren Landessprachen anzubieten. Die vollständige Unterstützung der Suite für vier Sprachen gewährleistet die Konformität, ohne dass kundenspezifische Entwicklung oder Integrationskomplexität erforderlich ist.

**Unterstützung mehrsprachiger Organisationen**: Organisationen, die in verschiedenen Schweizer Sprachregionen tätig sind, können eine einzige Plattforminstanz bereitstellen, die alle Regionen bedient, wobei die Benutzer die Oberfläche in ihrer bevorzugten Sprache erleben. Dies vereinfacht die Bereitstellung und Verwaltung im Vergleich zur Pflege separater sprachspezifischer Instanzen.

**Reduzierter Schulungsaufwand**: Schulungsmaterialien, Dokumentation und Benutzerunterstützung können in den Muttersprachen der Benutzer bereitgestellt werden, was die Akzeptanz beschleunigt und die Schulungskosten senkt, verglichen mit der Anforderung, dass Benutzer in nicht-muttersprachlichen Sprachen arbeiten.

**Gleichberechtigter Zugang**: Indem alle vier Sprachen als gleichberechtigt behandelt werden, anstatt eine Primärsprache mit minderwertigen Übersetzungen in anderen zu haben, stellt die Suite sicher, dass keine Sprachgemeinschaft eine eingeschränkte Erfahrung erhält.

**Zukünftige Sprachunterstützung**: Die erweiterbare Übersetzungsarchitektur ermöglicht es Organisationen, zusätzliche Sprachen (regionale Dialekte, Sprachen von Einwanderergemeinschaften, Sprachen internationaler Niederlassungen) hinzuzufügen, sollten die Bereitstellungsanforderungen über die Schweiz hinausgehen.

## Technische Implementierungsdetails

Aus technischer Sicht implementiert das Internationalisierungssystem mehrere hochentwickelte Funktionen.

**Lazy Loading**: Übersetzungsdateien werden bei Bedarf und nicht im Voraus geladen, wodurch sichergestellt wird, dass Benutzer nur Übersetzungen für ihre ausgewählte Sprache herunterladen. Dies optimiert die anfängliche Seitenladeleistung, was besonders für Benutzer mit langsameren Verbindungen wichtig ist.

**Parametersubstitution**: Übersetzungen unterstützen parametrisierte Nachrichten, bei denen Variablenwerte in den übersetzten Text eingefügt werden. Eine Übersetzung wie „Willkommen, \{name}!‟ positioniert den Namensparameter korrekt gemäß den grammatischen Regeln der Zielsprache.

**Pluralisierung**: Das Übersetzungssystem behandelt Pluralformen sprachübergreifend korrekt und erkennt, dass verschiedene Sprachen unterschiedliche Pluralisierungsregeln haben. Die einfache Singular-/Plural-Unterscheidung des Englischen unterscheidet sich von komplexeren Mustern in anderen Sprachen.

**Datum- und Zahlenformatierung**: Das System verwendet gebietsschema-bewusste Formatierungsbibliotheken, die automatisch die korrekten Formatierungsregeln basierend auf der Sprachauswahl des Benutzers anwenden, wodurch die Notwendigkeit für Entwickler entfällt, gebietsschema-spezifische Formatierungslogik zu implementieren.

## Kontinuierliche Verbesserung

Internationalisierung ist keine einmalige Implementierung, sondern eine fortlaufende Verpflichtung zur Aufrechterhaltung der Qualität über alle Sprachen hinweg.

**Übersetzungsaktualisierungen**: Wenn sich Oberflächentexte ändern oder neue Funktionen hinzugefügt werden, werden Übersetzungen durch koordinierte Prozesse aktualisiert, die sicherstellen, dass alle Sprachen mit den Plattformfunktionen auf dem neuesten Stand bleiben.

**Integration von Benutzerfeedback**: Benutzer können Übersetzungsprobleme – falsche Terminologie, unglückliche Formulierungen, fehlende Übersetzungen – über Feedback-Mechanismen melden. Dieser Input fließt in die Übersetzungsverfeinerungszyklen ein.

**Professionelle Überprüfungszyklen**: Periodisch werden Übersetzungen einer professionellen Überprüfung durch Muttersprachler mit technischer Expertise unterzogen, um sicherzustellen, dass die Qualität professionellen Standards entspricht, während sich die Plattform weiterentwickelt.

**Potenzial für maschinelles Lernen**: Mit fortschreitenden KI-Fähigkeiten könnte die Plattform Sprachmodelle nutzen, um Verbesserungen bei Übersetzungen vorzuschlagen, potenzielle Inkonsistenzen zu kennzeichnen oder sogar Entwurfsübersetzungen für die menschliche Überprüfung zu generieren.

Dieser umfassende Internationalisierungsansatz stellt sicher, dass die Swiss AI Hub Suite einen wirklich gleichberechtigten Zugang über die sprachliche Vielfalt der Schweiz hinweg bietet und die Mission der Plattform unterstützt, KI-Fähigkeiten allen Schweizer Organisationen und Gemeinschaften unabhängig von der Sprachpräferenz zugänglich zu machen.
