---
title: Grundlagen von Agenten
index: 1
source_sha: "db857bafafdffe40baec55955eea138e87e2c244e5f67c340a7469b85b402870"
---

# Grundlagen von Agenten

Während der Benutzer mit Agenten über eine einfache Chat-Oberfläche interagiert, arbeitet im Hintergrund eine hochentwickelte, ereignisgesteuerte Architektur, die sie zuverlässig, auditierbar und intelligent macht. Dieser Abschnitt beleuchtet die grundlegenden Konzepte, die das Funktionieren, die Informationsverwaltung und die Zusammenarbeit von Agenten im Swiss AI Hub steuern.

Das Verständnis dieser Prinzipien ist entscheidend, um zu würdigen, wie die Plattform KI von einer unberechenbaren „Black Box“ in ein transparentes und vertrauenswürdiges Unternehmenswerkzeug verwandelt.

## Der Bauplan des Agenten: Strukturierte Workflows

Das Verhalten jedes Agenten wird durch einen **Workflow** definiert – einen expliziten, Schritt-für-Schritt-Prozess. Dies ist das wichtigste Designprinzip der Plattform. Anstatt einem Agenten eine Reihe von Tools zu geben und ihn autonom entscheiden zu lassen, wie er diese verwendet, definieren wir die genaue Abfolge der Operationen, die er ausführen muss.

Dieser strukturierte Ansatz bietet die Vorhersehbarkeit und Kontrolle, die Unternehmen benötigen:

-   **Transparenz**: Jeder, vom Entwickler bis zum Compliance Officer, kann die Workflow-Definition einsehen und die Logik des Agenten verstehen. Dies macht das KI-Verhalten erklärbar.
-   **Zuverlässigkeit & Testbarkeit**: Jeder Schritt in einem Workflow kann unabhängig entwickelt und getestet werden. Dies reduziert das Bereitstellungsrisiko und stellt sicher, dass komplexe Prozesse aus zuverlässigen Komponenten aufgebaut sind.
-   **Kontrolle**: Der Agent wird durch seinen Workflow eingeschränkt. Er kann nicht entscheiden, auf Daten zuzugreifen, die er nicht sollte, oder Aktionen außerhalb seiner vordefinierten Sequenz ausführen, wodurch eine erhebliche Klasse von Risiken eliminiert wird, die mit autonomer KI verbunden sind.

Innerhalb jedes Schritts kann der Agent die volle Leistungsfähigkeit der KI nutzen, um zu urteilen, Daten zu analysieren und intelligente Entscheidungen zu treffen, aber sein gesamter Pfad wird durch den von Ihnen definierten Workflow gesteuert.

## Das Gedächtnis des Agenten: Hierarchisches Kontextmanagement

Damit ein Agent effektiv ist, insbesondere in einer langen Konversation, benötigt er ein Gedächtnis. Die Plattform bietet ein ausgeklügeltes, mehrschichtiges Kontextmanagementsystem, das als Gedächtnis des Agenten fungiert und sicherstellt, dass er nie den Überblick über die Konversation verliert, während die Leistung optimiert wird.

Dieses Gedächtnis ist in einer dreistufigen Hierarchie organisiert:

-   **Thread Context**: Dies ist das **Langzeitgedächtnis** des Agenten für eine gesamte Konversation oder einen lang andauernden Geschäftsprozess. Es speichert Benutzerpräferenzen, den vollständigen Konversationsverlauf und über mehrere Interaktionen hinweg angesammeltes Wissen. Wenn Sie zu einer Konversation zurückkehren, die Sie gestern begonnen haben, ermöglicht der Thread Context dem Agenten, sich an alles zu erinnern, was Sie besprochen haben. Er ist die Grundlage für Sicherheit, da der Zugriff auf Thread-Ebene kontrolliert wird.

-   **Display Context**: Dieser Bereich verwaltet, was dem Benutzer in der Oberfläche angezeigt wird. Er gruppiert eine Reihe von Aktionen, um sie als eine einzige, nahtlose Interaktion darzustellen. Dies ist besonders wichtig, wenn Agenten im Hintergrund zusammenarbeiten, da es einem primären Agenten ermöglicht zu steuern, ob die „Arbeit“ eines Sub-Agenten für den Benutzer sichtbar oder verborgen ist.

-   **Run Context**: Dies ist das **Kurzzeit-Arbeitsgedächtnis** des Agenten für eine einzelne, nachvollziehbare Aufgabe (z.B. von Ihrer Frage bis zu ihrer Antwort). Es enthält die Zwischenberechnungen, temporären Daten und die unveränderliche Konfiguration für diese spezifische Ausführung. Dieses Gedächtnis ist flüchtig und für einen schnellen Zugriff während des Betriebs des Agenten optimiert.

<h2>Das Ökosystem des Agenten: Ereignisgesteuerte Teilnehmer</h2>

Ein Agent arbeitet nicht isoliert. Er ist Teil eines Ökosystems von Komponenten, die zusammenarbeiten, um eine nahtlose und sichere Erfahrung zu liefern. Diese Interaktion ist vollständig **ereignisgesteuert**, was bedeutet, dass Komponenten über asynchrone Nachrichten auf einem zentralen Nachrichtenbus kommunizieren. Dieses Design macht das System hochskalierbar, widerstandsfähig und perfekt auditierbar.

Es gibt vier Hauptteilnehmer in diesem Ökosystem:

1.  **Der Agent**: Der autonome Worker, der die in seinem Workflow definierte Geschäftslogik ausführt. Er konsumiert Anweisungen (Control Events) und erzeugt einen reichhaltigen Strom von Ergebnissen und Telemetrie (Display Events).
2.  **Das API Gateway**: Die sichere Eingangstür zur Plattform. Es ist die einzige Komponente, die initiale Events aus externen Anfragen erzeugen kann. Es authentifiziert Benutzer, übersetzt ihre HTTP-Anfragen in sichere interne Events und streamt die Antworten des Agenten zurück zur Benutzeroberfläche.
3.  **Das Frontend**: Die Benutzeroberfläche, mit der Sie interagieren. Es ist hauptsächlich ein Listener, der einen Strom von „Display Events“ vom Agenten abonniert und diese in Echtzeit als Streaming-Text, Denkprozesse oder andere UI-Elemente rendert.
4.  **Der Process Orchestrator**: Ein spezialisierter Agententyp, der High-Level-Geschäftsprozesse verwaltet. Er agiert wie ein Dirigent, indem er die Abschlussereignisse eines Agenten konsumiert, um den nächsten Teilnehmer in einem komplexen, mehrstufigen Workflow auszulösen.

Diese entkoppelte Architektur gewährleistet die Robustheit der Plattform. Eine Verlangsamung der Benutzeroberfläche kann beispielsweise den Workflow des zugrunde liegenden Agenten nicht zum Absturz bringen.

## Erweiterte Funktionen: Kollaborationsmuster

Die Architektur der Plattform ermöglicht ausgeklügelte Kollaborationsmuster, die es Agenten ermöglichen, effektiv miteinander und mit menschlichen Benutzern zusammenzuarbeiten.

### Human-in-the-Loop: Integration menschlichen Urteilsvermögens

Nicht jede Entscheidung kann oder sollte vollständig automatisiert werden. Die Plattform ist mit „Human-in-the-Loop“-Funktionen als Kernmerkmal ausgestattet, die es Workflows ermöglichen, menschliche Aufsicht nahtlos zu integrieren.

::: details So funktioniert's
Der Workflow eines Agenten kann so konzipiert werden, dass er an jedem kritischen Schritt pausiert und ein `HumanInTheLoopRequestEvent` veröffentlicht. Dieses Ereignis erstellt eine Aufgabe in der Benutzeroberfläche des Benutzers, die ihm den notwendigen Kontext und die Auswahlmöglichkeiten präsentiert. Der Workflow bleibt pausiert – für Minuten, Stunden oder sogar Tage – bis der Benutzer antwortet. Nach der Antwort wird ein `HumanInTheLoopResponseEvent` generiert, und der Workflow des Agenten wird fortgesetzt.
:::

Dieses Muster ist weitaus leistungsfähiger als einfache Benutzereingaben.

-   **Echte Kontexterhaltung**: Der Workflow wird nach menschlicher Eingabe nicht neu gestartet. Er wird ab dem **genauen Punkt fortgesetzt, an dem er pausiert wurde**, mit vollständiger Erinnerung an alle Zwischenergebnisse und vorherigen Schritte. Dies ist entscheidend für komplexe, mehrstufige Prozesse.
-   **Vollständiger Audit Trail**: Jede menschliche Interaktion – die gestellte Frage, wer geantwortet hat, was entschieden wurde und wann – wird unveränderlich als Ereignis protokolliert, um die volle Rechenschaftspflicht für Compliance und Auditing zu gewährleisten.
-   **Flexibilität bei Anwendungsfällen**: Dies ermöglicht kritische Unternehmensszenarien, von Genehmigungen und Qualitätskontrollen bis hin zur Bearbeitung mehrdeutiger Situationen, in denen ein Agent Klärung benötigt. Es ermöglicht auch Benutzerzustimmungs-Workflows, bei denen ein Agent einen Haftungsausschluss präsentiert, den ein Benutzer akzeptieren muss, bevor der Prozess fortgesetzt werden kann.

### Agent-zu-Agent-Delegation: Ein Team von Spezialisten

Komplexe Probleme werden oft am besten von einem Team von Spezialisten gelöst. Die Plattform ermöglicht dies, indem ein primärer Agent Aufgaben an andere, spezialisiertere Agenten delegieren kann, indem er ein `AgentInTheLoop`-Ereignismuster verwendet.

Ein allgemeiner „Dokumenten-Anfrage-Agent“ könnte beispielsweise eine komplexe Rechtsfrage erhalten. Anstatt zu versuchen, diese selbst zu beantworten, kann er die Aufgabe an einen spezialisierten „Rechts-Compliance-Agenten“ delegieren.

Dieses Muster ermöglicht es Ihnen, ein leistungsfähiges, zusammensetzbares System von KI-Funktionen aufzubauen:
-   **Wiederverwendbarkeit**: Bauen Sie fokussierte, wiederverwendbare Agenten für spezifische Aufgaben (z.B. Entitätenextraktion, PII-Erkennung, Compliance-Prüfung) und orchestrieren Sie diese, um größere Geschäftsprobleme zu lösen.
-   **Isolation und Sicherheit**: Der delegierte Agent läuft in seinem eigenen isolierten Workflow. Er kann nicht auf den internen Zustand des primären Agenten zugreifen, wodurch Sicherheit gewährleistet und unbeabsichtigte Nebenwirkungen verhindert werden.
-   **Kontrolle über die Sichtbarkeit**: Der primäre Agent steuert den `Display Context` und entscheidet, was der Benutzer sieht. Er kann die Zusammenarbeit transparent machen, indem er dem Benutzer zeigt, dass er einen anderen Experten konsultiert, oder es kann vollständig im Hintergrund geschehen, wobei der Benutzer nur die endgültige, konsolidierte Antwort sieht.
-   **Skalierbarkeit**: Spezialisierte, stark nachgefragte Agenten können unabhängig skaliert werden, um sicherzustellen, dass Engpässe in einer Funktion das gesamte System nicht verlangsamen.
