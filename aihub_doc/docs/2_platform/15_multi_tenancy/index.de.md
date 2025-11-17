---
title: Mandantenfähigkeit
source_sha: 1586a91f8246563bdcd02280a2e960ad94fdcef027d69fccf96f56e632dacf5d
---

# Mandantenfähigkeit

Mandantenfähigkeit ermöglicht es Ihnen, organisatorische Grenzen innerhalb einer einzelnen Plattforminstanz zu schaffen.
Jeder Mandant repräsentiert einen Arbeitsbereich mit eigenen Benutzern, Rollen sowie Zugriff auf Agents und Services.

Das mandantenfähige Modell der Plattform bietet Ihnen die Flexibilität, den Zugriff so zu strukturieren, dass er den
Anforderungen Ihrer Organisation entspricht, von einfacher Abteilungsseparation bis hin zu komplexen hierarchischen
Konfigurationen.

## Drei Ressourcentypen

Die Plattform stellt drei Arten von Ressourcen bereit:

**Services** sind Plattformfunktionen wie Benutzerverwaltung, Wissensdatenbankverwaltung, Agentenbewertung und
Systemkonfiguration. Die meisten Benutzer benötigen keinen direkten Servicezugriff.

**Agents** sind KI-Assistenten, die spezifische Aufgaben ausführen. Benutzer interagieren mit Agents über Chat oder
Agents führen Aufgaben autonom aus. Agents greifen auf Daten zu und führen Aktionen basierend auf ihrer Konfiguration
aus.

**Processes** orchestrieren Workflows, die mehrere Agents, menschliche Genehmigungen und externe Systeme umfassen.
Processes koordinieren komplexe Geschäftsabläufe.

## Das Agenten-Unabhängigkeitsprinzip

::: info The Most Important Concept
**Agents agieren unabhängig von Benutzer- und Mandantenberechtigungen.**

Wenn ein Benutzer mit einem Agent chattet, erbt der Agent nicht die ZugriffsBeschränkungen dieses Benutzers. Der Agent
greift auf Daten basierend auf seiner eigenen Konfiguration zu. Dies hat weitreichende Implikationen für die
Strukturierung von Mandanten und die Kontrolle des Datenzugriffs.
:::

Warum dieses Design? Agents müssen oft:

- Auf Daten aus mehreren Quellen zugreifen, die einzelne Benutzer nicht sehen können
- Autonom ohne Benutzerinteraktion laufen
- An Gruppenkonversationen mit Benutzern teilnehmen, die unterschiedliche Berechtigungen haben
- Geplante Aufgaben ausführen, unabhängig davon, wer online ist

Sie steuern den Datenzugriff, indem Sie festlegen, welche Benutzer mit welchen Agents interagieren können. Die
Konfiguration des Agenten bestimmt, auf welche Daten er zugreifen kann. Ihr Mandantendesign bestimmt, wer diesen Agenten
verwenden kann.

## Gängige Muster

Die meisten Organisationen verwenden eine dreistufige Struktur:

**Systemadministrator-Ebene**: Ein Mandant für Plattformadministratoren, die Agents entwickeln, Pipelines deployen und
die Infrastruktur warten. Diese Benutzer sehen alles und können systemweite Konfigurationen ändern.

**Management-Ebene**: Ein Mandant für Personen, die die Plattform für Geschäftsanwender verwalten. Sie erstellen
Mandanten, weisen Benutzern Mandanten zu, konfigurieren Agent-Instanzen und überwachen die Nutzung. Sie können keinen
neuen Agent-Code deployen oder die Infrastruktur ändern.

**Abteilungsebenen**: Ein Mandant pro Abteilung, Geschäftseinheit oder Kunde. Benutzer arbeiten mit Agents, die für ihre
Abteilung relevant sind. Sie können keine Agents anderer Abteilungen sehen oder auf administrative Funktionen zugreifen.

Diese Struktur trennt technische Operationen, Geschäftsverwaltung und den täglichen Gebrauch.

## Flexibilität und Verantwortung

Das System ist absichtlich flexibel. Sie können permissive Konfigurationen erstellen, bei denen Agents auf alle Daten
zugreifen, oder restriktive Setups, bei denen Agents nur eng gefassten Zugriff auf spezifische Informationen haben.

Diese Flexibilität bedeutet, dass Sie verantwortlich sind für:

- Das Design einer Mandantenstruktur, die Ihren Sicherheitsanforderungen entspricht
- Die Konfiguration von Agents mit entsprechendem Datenzugriff
- Die Zuweisung von Benutzern zu den richtigen Mandanten mit entsprechenden Rollen
- Die regelmäßige Überprüfung, wer auf welche Agents zugreifen kann

Die Plattform setzt die von Ihnen definierten Grenzen durch. Sie wird Sie nicht daran hindern, einen Agent zu erstellen,
der auf alles zugreift und diesen Agent jedem zur Verfügung zu stellen. Das ist eine gültige Konfiguration, wenn sie
Ihren Anforderungen entspricht – aber Sie müssen die Implikationen verstehen.
