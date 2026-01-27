---
title: Benutzerspeicher
source_sha: "3e35bc92f20b2536af171eb63cb82c8de985c40de47869c7b967682e1457e7ab"
---

# Benutzerspeicher

Der Benutzerspeicher ermöglicht es KI-Agents, Ihre persönlichen Präferenzen, Ihren Arbeitsstil und Ihren individuellen Kontext zu lernen. Dieser Speicher ist privat und nur für Sie zugänglich – kein anderer Benutzer kann sehen, was Agents über Ihre Präferenzen gelernt haben. Im Laufe der Zeit passen Agents ihr Verhalten an Ihre Arbeitsweise an.

## Was gespeichert wird

Agents lernen automatisch Informationen, die ihnen helfen, Sie besser zu unterstützen. Dazu gehören Ihre bevorzugten Programmiersprachen, Ihr Kommunikationsstil, der Detailgrad in den Antworten und Ihre Formatierungspräferenzen. Wenn Sie konsequent prägnante Antworten wünschen, lernen Agents, sich kurz zu fassen. Wenn Sie detaillierte Erklärungen mit Beispielen bevorzugen, passen sie sich entsprechend an.

Agents lernen auch Ihren Technologie-Stack, aktuelle Projekte, typische Aufgaben und Fachgebiete. Wenn Sie häufig über Python-Entwicklung sprechen, erkennen Agents dies und formulieren technische Vorschläge in Python-Terminologie. Auch Prozessmuster wie Ihre bevorzugte Genehmigungshandhabung, Ihre typischen Arbeitszeiten und Workflow-Gewohnheiten werden erfasst.

Benutzerspeicher sind streng auf Ihr Konto isoliert. Wenn ein Agent lernt, dass Sie detaillierte Code-Kommentare bevorzugen, betrifft diese Präferenz nur Ihre Interaktionen. Andere Benutzer bevorzugen möglicherweise minimale Kommentare, und ihre Agents passen sich anders an. Diese Isolation erstreckt sich über Agent-Typen hinweg – jeder Agent lernt Präferenzen, die für seine Funktion relevant sind, ohne andere zu beeinträchtigen.

## Wie es funktioniert

Der Benutzerspeicher erfordert keinen manuellen Aufwand. Während Sie mit Agents interagieren, analysieren diese die Konversation, um nützliche, speicherwürdige Informationen zu identifizieren. Nach der Verarbeitung Ihrer Konversation fragt sich der Agent: „Was habe ich über die Präferenzen oder den Kontext dieses Benutzers gelernt, das mir helfen würde, ihn in Zukunft besser zu unterstützen?“

Dieser Ansatz bedeutet, dass Sie keine Präferenzlisten pflegen oder Profilformulare ausfüllen müssen. Agents lernen aus Ihrer tatsächlichen Arbeitsweise, nicht aus dem, wie Sie glauben zu arbeiten. Wenn sich Ihre Präferenzen entwickeln, spiegeln neue Speicherungen diese Änderungen wider.

Verschiedene Agent-Typen konzentrieren sich auf unterschiedliche Aspekte. Code-Assistenten lernen Ihre bevorzugten Sprachen, Frameworks, den Codierungsstil und die Arten von Beispielen, die Sie hilfreich finden. Wissensabfrage-Agents lernen, welche Themen Sie interessieren, Ihre bevorzugte Informationstiefe und wie Sie Quellen zitiert haben möchten. Prozess-Orchestrierungs-Agents lernen Ihre Genehmigungsschwellenwerte, Benachrichtigungspräferenzen und wie Sie mit automatisierten Workflows interagieren.

Agents behalten die Übersicht, wann Speicherungen erstellt wurden. Wenn Sie vor sechs Monaten die Arbeit am „neuen Dashboard-Projekt“ erwähnt haben und es heute erneut erwähnen, versteht der Agent, dass dies unterschiedliche Projekte oder verschiedene Phasen desselben Projekts sein könnten.

## Ihre Speicherungen einsehen

Greifen Sie über die Navigation der Plattform auf den Service **Benutzerspeicher** zu, um alles zu sehen, was Agents über Sie gelernt haben. Jede Speicherung zeigt die tatsächlich erinnerte Information (z.B. „Benutzer bevorzugt Python gegenüber JavaScript für die Backend-Entwicklung“), wann diese Speicherung gelernt wurde, welcher Agent diese Präferenz identifiziert hat und den Thread, aus dem diese Information stammt. Sie können zur Quellkonversation klicken, um den genauen Kontext zu sehen, der die Speicherung generiert hat.

Die Oberfläche unterstützt die semantische Suche. Anstelle einer exakten Stichwortsuche können Sie nach Bedeutung suchen. Die Suche nach „Programmiersprachen“ findet Speicherungen über Ihre Python-Präferenz, JavaScript-Erfahrung und TypeScript-Interessen, auch wenn diese exakten Wörter nicht in Ihrer Suche erscheinen.

Einige Speicherungen sind durch Beziehungen miteinander verbunden. Wenn Agents lernen, dass Sie „an Projekt Falcon arbeiten“ und „Projekt Falcon Microservices verwendet“, kann die Oberfläche diese Verbindungen als Graph darstellen, um Ihnen zu helfen zu verstehen, wie Agents verschiedene Informationen über Ihren Kontext miteinander verknüpfen.

## Ihre Speicherungen verwalten

Klicken Sie auf eine beliebige Speicherung, um deren Inhalt zu bearbeiten. Dies ist nützlich, wenn ein Agent etwas leicht Falsches gelernt hat, sich Ihre Präferenzen geändert haben oder Sie die Ausdrucksweise verfeinern möchten. Das Bearbeiten einer Speicherung beeinflusst sofort, wie Agents diese Information nutzen – wenn Sie „Benutzer bevorzugt prägnante Antworten“ in „Benutzer bevorzugt detaillierte Erklärungen mit Beispielen“ korrigieren, passen Agents ihr Verhalten in der nächsten Konversation an.

Sie können einzelne Speicherungen, die nicht mehr relevant oder korrekt sind, löschen oder alle Ihre Benutzerspeicherungen auf einmal löschen. Häufige Gründe sind Rollenwechsel, die alte technische Präferenzen irrelevant machen, abgeschlossene Projekte, deren Kontext nicht mehr zutrifft, Datenschutzbedenken bezüglich spezifischer Informationen oder der Wunsch, dass Agents Ihre Präferenzen von Grund auf neu lernen. Die Löschung ist sofortig und irreversibel.

::: info DSGVO-Konformität
Die Plattform unterstützt Ihre Datenschutzrechte vollständig: Auskunft (alle Speicherungen einsehen), Berichtigung (jede Speicherung bearbeiten), Löschung (spezifische oder alle Speicherungen löschen) und Datenportabilität (Export über API). Das Löschen aller Benutzerspeicherungen erfüllt Ihr Recht auf Vergessenwerden bezüglich Präferenzdaten.
:::

## Praktische Beispiele

### Anpassung des Code-Assistenten

In der ersten Woche bitten Sie einen Code-Assistenten um Hilfe bei einer Python-Funktion. Der Agent erstellt eine Speicherung: „Benutzer arbeitet mit Python.“ In der folgenden Woche fragen Sie nach der Authentifizierung. Ohne dass Sie es explizit sagen, liefert der Agent Python-Beispiele anstelle anderer Sprachen. Er bemerkt auch, dass Sie Inline-Kommentare schätzen, und erstellt eine weitere Speicherung über Ihre Dokumentationspräferenzen. Bis zur vierten Woche, wenn Sie nach einem komplexen Algorithmus fragen, liefert der Agent automatisch Python-Code mit detaillierten Kommentaren, da er beide Präferenzen aus Ihrem tatsächlichen Verhalten gelernt hat.

### Personalisierung der Wissensabfrage

Sie fragen einen Wissens-Agenten nach maschinellem Lernen und erhalten einen umfassenden Überblick. Der Agent merkt sich Ihr Interesse. Wenn Sie nach weiteren Details zu einem bestimmten Aspekt fragen, bietet er technische Tiefe und merkt sich, dass Sie detaillierte technische Erklärungen gegenüber hochrangigen Zusammenfassungen bevorzugen. In späteren Interaktionen zu verschiedenen Themen bietet der Agent automatisch eine ähnliche Tiefe und erwähnt proaktiv Verbindungen zum maschinellen Lernen.

### Lernen des Prozess-Agenten

Ein Prozess-Agent fordert Sie auf, ein Dokument zu genehmigen. Sie genehmigen mit Kommentaren zur Formatierung, und der Agent lernt, dass Sie die Formatierung vor der Genehmigung überprüfen. Bei nachfolgenden Anfragen nimmt er die Formatierungsprüfung in seine Vorab-Genehmigungs-Checkliste auf. Im Laufe der Zeit lernt er auch, wann Sie Genehmigungsanfragen basierend auf Ihren Antwortmustern erhalten möchten.

## Speicherentwicklung

Benutzerspeicher sind nicht statisch. Frühe Speicherungen können breit gefächert sein: „Benutzer arbeitet mit Webentwicklung.“ Spätere Speicherungen verfeinern dies: „Benutzer ist spezialisiert auf Frontend-Entwicklung mit Vue.js und TypeScript.“ Agents löschen die frühere Speicherung nicht – beide bleiben erhalten. Die spezifischere Speicherung hat Vorrang, wenn relevant, während die breitere Speicherung in allgemeinen Kontexten angewendet wird.

Wenn Sie einer früheren Präferenz explizit widersprechen, können Agents dies erkennen. Wenn sie gelernt haben „Benutzer bevorzugt prägnante Antworten“, Sie aber nach mehr Details fragen, erstellen sie eine neue Speicherung, die die Änderung widerspiegelt. Die Plattform bewahrt beide Speicherungen mit Zeitstempeln auf, sodass Agents verstehen können, dass sich Ihre Präferenzen entwickelt haben, anstatt den Widerspruch als Fehler zu behandeln.

Agents entwickeln ein stärkeres Vertrauen in Präferenzen, die sie wiederholt beobachten. Eine einmalige Interaktion erzeugt eine vorläufige Speicherung; konsistentes Verhalten verstärkt die Bedeutung dieser Speicherung.

## Best Practices

Versuchen Sie nicht, Agents durch künstliche Aussagen über Ihre Präferenzen zu „programmieren“. Arbeiten Sie natürlich, und Agents lernen aus Ihrem tatsächlichen Verhalten. Dies führt zu genaueren Speicherungen, als wenn Sie Präferenzen im Voraus diktieren würden.

Überprüfen Sie gelegentlich Ihre Benutzerspeicherungen, um zu sehen, was Agents gelernt haben. Dies hilft Ihnen, falsche Schlussfolgerungen frühzeitig zu erkennen, zu verstehen, warum Agents sich auf bestimmte Weisen verhalten, und zu entscheiden, ob Sie gelernte Präferenzen anpassen möchten. Wenn ein Agent etwas Falsches gelernt hat, bearbeiten Sie die Speicherung direkt, anstatt zu versuchen, sie durch Konversation zu korrigieren – direktes Bearbeiten ist schneller und zuverlässiger.

Der Benutzerspeicher ist so konzipiert, dass er im Hintergrund arbeitet. Sie müssen nicht ständig darüber nachdenken. Die Transparenzfunktionen dienen der Verifizierung und Kontrolle, nicht weil Sie das System aktiv verwalten müssten.

::: details Wie sich der Speicher auf die Performance auswirkt
Benutzerspeicherungen werden zu Beginn jeder Konversation mit einem Agent abgerufen. Der Abruf fügt minimale Latenz hinzu – typischerweise unter 100ms. Die semantische Suche stellt sicher, dass nur relevante Speicherungen in den Kontext des Agenten aufgenommen werden.
:::

::: details Speicherlimits
Das System legt keine harten Limits für die Anzahl der Benutzerspeicherungen fest. Agents konzentrieren sich auf die relevantesten Speicherungen für jede Konversation. Tausende von Speicherungen verlangsamen Interaktionen nicht, da nur relevante Informationen abgerufen werden.
:::

::: details Agentenübergreifende Speicherungsteilung
Während sich jeder Agent-Typ auf das spezialisiert, was er lernt, können faktische Speicherungen (nicht Präferenzen) agentenübergreifend geteilt werden. Wenn ein Agent lernt „Benutzer arbeitet an Projekt Falcon“, können andere Agents auf diesen faktischen Kontext zugreifen. Präferenzen wie „Benutzer bevorzugt prägnante Antworten“ bleiben agentenspezifisch.
:::
