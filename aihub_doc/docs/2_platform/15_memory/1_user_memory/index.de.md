---
title: Benutzerspeicher
source_sha: 663814adfa2a7fe43d91210662117c1605061de4289f0d9fd427de906785b2c7
---

# Benutzerspeicher

Der Benutzerspeicher ermöglicht es KI-Agents, Ihre persönlichen Präferenzen, Ihren Arbeitsstil und Ihren individuellen
Kontext zu erlernen. Dieser Speicher ist privat für Sie – kein anderer Benutzer kann sehen, was Agents über Ihre
Präferenzen gelernt haben. Im Laufe der Zeit passen Agents ihr Verhalten an Ihre Arbeitsweise an.

## Was gespeichert wird

Agents lernen automatisch Informationen, die ihnen helfen, Sie besser zu unterstützen. Dazu gehören Ihre bevorzugten
Programmiersprachen, Ihr Kommunikationsstil, der Detaillierungsgrad der Antworten und Formatpräferenzen. Wenn Sie
konsequent prägnante Antworten wünschen, lernen Agents, sich kurz zu fassen. Wenn Sie detaillierte Erklärungen mit
Beispielen bevorzugen, passen sie sich entsprechend an.

Agents lernen auch Ihren Technologie-Stack, aktuelle Projekte, typische Aufgaben und Fachgebiete. Wenn Sie häufig über
Python-Entwicklung sprechen, erkennen Agents dies und formulieren technische Vorschläge in Python-Begriffen.
Prozessmuster wie Ihre bevorzugte Genehmigungshandhabung, Ihre typischen Arbeitszeiten und Workflow-Gewohnheiten werden
ebenfalls erfasst.

Benutzerspeicher sind streng auf Ihr Konto isoliert. Wenn ein Agent lernt, dass Sie detaillierte Code-Kommentare
bevorzugen, betrifft diese Präferenz nur Ihre Interaktionen. Andere Benutzer bevorzugen möglicherweise minimale
Kommentare, und deren Agents passen sich anders an. Diese Isolation erstreckt sich über Agent-Typen hinweg – jeder Agent
lernt Präferenzen, die für seine Funktion relevant sind, ohne andere zu beeinträchtigen.

## Wie es funktioniert

Der Benutzerspeicher erfordert keinen manuellen Aufwand. Während Sie mit Agents kommunizieren, analysieren diese die
Konversation, um nützliche Informationen zu identifizieren, die es wert sind, gespeichert zu werden. Nach der
Verarbeitung Ihrer Konversation fragt sich der Agent: „Was habe ich über die Präferenzen oder den Kontext dieses
Benutzers gelernt, das mir helfen würde, ihn in Zukunft besser zu bedienen?"

Dieser Ansatz bedeutet, dass Sie keine Präferenzlisten pflegen oder Profilformulare ausfüllen müssen. Agents lernen aus
Ihrer tatsächlichen Arbeitsweise, nicht aus dem, wie Sie denken, dass Sie arbeiten. Wenn sich Ihre Präferenzen
entwickeln, spiegeln neue Speicher diese Änderungen wider.

Verschiedene Agent-Typen konzentrieren sich auf unterschiedliche Aspekte. Code-Assistenten lernen Ihre bevorzugten
Sprachen, Frameworks, Kodierungsstile und die Arten von Beispielen, die Sie hilfreich finden. Wissensabruf-Agents
lernen, welche Themen Sie interessieren, Ihre bevorzugte Informationstiefe und wie Sie Quellen zitiert haben möchten.
Prozessorchestrierungs-Agents lernen Ihre Genehmigungsschwellenwerte, Benachrichtigungspräferenzen und wie Sie mit
automatisierten Workflows interagieren.

Agents behalten die Übersicht darüber, wann Speicher erstellt wurden. Wenn Sie vor sechs Monaten die Arbeit an „dem
neuen Dashboard-Projekt“ erwähnt und es heute erneut ansprechen, versteht der Agent, dass es sich um unterschiedliche
Projekte oder verschiedene Phasen desselben Projekts handeln könnte.

## Ihre Speicher anzeigen

Greifen Sie über die Navigation der Plattform auf den Service **Benutzerspeicher** zu, um alles zu sehen, was Agents
über Sie gelernt haben. Jeder Speicher zeigt die tatsächlich gemerkte Information (z.B. „Benutzer bevorzugt Python
gegenüber JavaScript für die Backend-Entwicklung“), wann dieser Speicher gelernt wurde, welcher Agent diese Präferenz
identifiziert hat und den Thread, in dem diese Information ihren Ursprung hatte. Sie können zur Quellkonversation
klicken, um den genauen Kontext zu sehen, der den Speicher generiert hat.

Die Oberfläche unterstützt die semantische Suche. Anstelle einer exakten Keyword-Übereinstimmung können Sie nach
Bedeutung suchen. Die Suche nach „Programmiersprachen“ findet Speicher über Ihre Python-Präferenz, JavaScript-Erfahrung
und TypeScript-Interessen, selbst wenn diese genauen Wörter nicht in Ihrer Suche erscheinen.

Einige Speicher verbinden sich durch Beziehungen mit anderen. Wenn Agents lernen, dass Sie „an Projekt Falcon arbeiten“
und „Projekt Falcon Microservices verwendet“, kann die Oberfläche diese Verbindungen als Graph anzeigen und Ihnen helfen
zu verstehen, wie Agents verschiedene Informationsfragmente über Ihren Kontext miteinander verbinden.

## Ihre Speicher verwalten

Klicken Sie auf einen beliebigen Speicher, um dessen Inhalt zu bearbeiten. Dies ist nützlich, wenn ein Agent etwas
leicht Falsches gelernt hat, sich Ihre Präferenzen geändert haben oder Sie verfeinern möchten, wie etwas ausgedrückt
wird. Das Bearbeiten eines Speichers beeinflusst sofort, wie Agents diese Informationen verwenden – wenn Sie „Benutzer
bevorzugt prägnante Antworten“ in „Benutzer bevorzugt detaillierte Erklärungen mit Beispielen“ korrigieren, passen
Agents ihr Verhalten in der nächsten Konversation an.

Sie können einzelne Speicher löschen, die nicht mehr relevant oder korrekt sind, oder alle Ihre Benutzerspeicher auf
einmal löschen. Häufige Gründe dafür sind Rollenwechsel, die alte technische Präferenzen irrelevant machen,
abgeschlossene Projekte, deren Kontext nicht mehr zutrifft, Datenschutzbedenken bezüglich spezifischer Informationen
oder der Wunsch, dass Agents Ihre Präferenzen von Grund auf neu lernen. Das Löschen ist sofort und irreversibel.

::: info GDPR-Konformität
Die Plattform unterstützt Ihre Datenschutzrechte vollumfänglich: Zugriff (alle Speicher anzeigen), Berichtigung (jeden
Speicher bearbeiten), Löschung (bestimmte oder alle Speicher löschen) und Datenportabilität (Export über API). Das
Löschen aller Benutzerspeicher erfüllt Ihr Recht auf Vergessenwerden bezüglich Präferenzdaten.
:::

## Praktische Beispiele

### Anpassung des Code-Assistenten

In der ersten Woche bitten Sie einen Code-Assistenten um Hilfe bei einer Python-Funktion. Der Agent erstellt einen
Speicher: „Benutzer arbeitet mit Python.“ In der folgenden Woche fragen Sie nach der Authentifizierung. Ohne dass es
explizit gesagt werden muss, liefert der Agent Python-Beispiele anstatt anderer Sprachen. Er bemerkt auch, dass Sie
Inline-Kommentare schätzen, und erstellt einen weiteren Speicher über Ihre Dokumentationspräferenzen. Bis zur vierten
Woche, wenn Sie nach einem komplexen Algorithmus fragen, stellt der Agent automatisch Python-Code mit detaillierten
Kommentaren zur Verfügung, da er beide Präferenzen aus Ihrem tatsächlichen Verhalten gelernt hat.

### Personalisierung des Wissensabrufs

Sie fragen einen Wissens-Agenten nach maschinellem Lernen und erhalten eine umfassende Übersicht. Der Agent notiert Ihr
Interesse. Wenn Sie nach weiteren Details zu einem bestimmten Aspekt fragen, bietet er technische Tiefe und merkt sich,
dass Sie detaillierte technische Erklärungen gegenüber hochrangigen Zusammenfassungen bevorzugen. In späteren
Interaktionen zu verschiedenen Themen bietet der Agent automatisch eine ähnliche Tiefe und erwähnt proaktiv Verbindungen
zum maschinellen Lernen.

### Lernen des Prozess-Agenten

Ein Prozess-Agent bittet Sie, ein Dokument zu genehmigen. Sie genehmigen es mit Kommentaren zur Formatierung, und der
Agent lernt, dass Sie die Formatierung vor der Genehmigung überprüfen. Bei nachfolgenden Anfragen nimmt er die
Formatierungsüberprüfung in seine Vorab-Genehmigungs-Checkliste auf. Im Laufe der Zeit lernt er auch, wann Sie
Genehmigungsanfragen bevorzugt erhalten, basierend auf Ihren Antwortmustern.

## Speicherentwicklung

Benutzerspeicher sind nicht statisch. Frühe Speicher könnten breit gefächert sein: „Benutzer arbeitet mit
Webentwicklung.“ Spätere Speicher verfeinern dies: „Benutzer spezialisiert sich auf Frontend-Entwicklung unter
Verwendung von Vue.js und TypeScript.“ Agents löschen den früheren Speicher nicht – beide bleiben erhalten. Der
spezifischere Speicher hat Vorrang, wenn relevant, während der breitere Speicher in allgemeinen Kontexten angewendet
wird.

Wenn Sie einer früheren Präferenz explizit widersprechen, können Agents dies erkennen. Wenn sie gelernt haben „Benutzer
bevorzugt prägnante Antworten“, Sie aber nach mehr Details fragen, erstellen sie einen neuen Speicher, der die Änderung
widerspiegelt. Die Plattform bewahrt beide Speicher mit Zeitstempeln auf, sodass Agents verstehen können, dass sich Ihre
Präferenzen entwickelt haben, anstatt den Widerspruch als Fehler zu behandeln.

Agents entwickeln ein stärkeres Vertrauen in Präferenzen, die sie wiederholt beobachten. Eine einmalige Interaktion
erzeugt einen vorläufigen Speicher; konsistentes Verhalten verstärkt die Bedeutung dieses Speichers.

## Bewährte Praktiken

Versuchen Sie nicht, Agents durch künstliche Aussagen über Ihre Präferenzen zu „programmieren“. Arbeiten Sie natürlich,
und Agents werden aus Ihrem tatsächlichen Verhalten lernen. Dies führt zu genaueren Speichern, als Präferenzen im Voraus
diktieren zu wollen.

Überprüfen Sie gelegentlich Ihre Benutzerspeicher, um zu sehen, was Agents gelernt haben. Dies hilft Ihnen, falsche
Schlussfolgerungen frühzeitig zu erkennen, zu verstehen, warum Agents sich auf bestimmte Weisen verhalten, und zu
entscheiden, ob Sie gelernte Präferenzen anpassen möchten. Wenn ein Agent etwas Falsches gelernt hat, bearbeiten Sie den
Speicher direkt, anstatt zu versuchen, ihn durch Konversation zu korrigieren – direktes Bearbeiten ist schneller und
zuverlässiger.

Der Benutzerspeicher ist darauf ausgelegt, im Hintergrund zu arbeiten. Sie müssen nicht ständig darüber nachdenken. Die
Transparenzfunktionen existieren zur Überprüfung und Kontrolle, nicht weil Sie das System aktiv verwalten müssen.

::: details Wie sich der Speicher auf die Leistung auswirkt
Benutzerspeicher werden zu Beginn jeder Konversation mit einem Agent abgerufen. Der Abruf fügt eine minimale Latenz
hinzu – typischerweise unter 100ms. Die semantische Suche stellt sicher, dass nur relevante Speicher in den Kontext des
Agenten aufgenommen werden.
:::

::: details Speicherlimits
Das System legt keine festen Grenzen für die Anzahl der Benutzerspeicher fest. Agents konzentrieren sich auf die
relevantesten Speicher für jede Konversation. Tausende von Speichern verlangsamen die Interaktionen nicht, da nur
relevante Informationen abgerufen werden.
:::

::: details Speicherfreigabe zwischen Agents
Während sich jeder Agent-Typ auf das spezialisiert, was er lernt, können faktische Speicher (nicht Präferenzen) zwischen
Agents geteilt werden. Wenn ein Agent lernt „Benutzer arbeitet an Projekt Falcon“, können andere Agents auf diesen
faktischen Kontext zugreifen. Präferenzen wie „Benutzer bevorzugt prägnante Antworten“ bleiben Agent-spezifisch.
:::
