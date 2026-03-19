```yaml
---
title: Chatten mit Ihrem Unternehmenswissen
source_sha: "55eb499714e55d645419b00513f9fbbdef1c0345f3b5914783636efd151a1bf4"
---
# Chatten mit Ihrem Unternehmenswissen

Der Swiss AI Hub zeigt Benutzern, welche Wissensdokumente und Textpassagen KI-Antworten informiert haben. Diese Transparenz hilft Benutzern, die Richtigkeit zu überprüfen und die Grundlage für KI-Schlussfolgerungen zu verstehen.

## Warum dies wichtig ist

Wenn KI-Systeme Retrieval-Augmented Generation (RAG) mit organisationalen Wissensdatenbanken verwenden, müssen Benutzer überprüfen können, woher die Informationen stammen. Standard-Chat-Interfaces, einschliesslich nativer Open WebUI, zeigen nicht systematisch an, welche Dokumente oder Passagen die Antworten informiert haben.

Regulierte Industrien und qualitätskritische Bereiche erfordern Nachweisketten für KI-generierte Inhalte. Entscheidungsträger müssen überprüfen, ob die Antworten mit massgeblichen Quellen und aktuellen Richtlinien übereinstimmen. Ohne Quellenangabe erfordert die Verifizierung manuelle Recherche.

Organisationen, die Wissensdatenbanken pflegen, benötigen Feedback zur Qualität des Retrievals. Die Quellenangabe zeigt, ob Agents auf geeignete Dokumente zugreifen und deckt Wissenslücken für häufige Anfragen auf.

## Wie es funktioniert

Ein benutzerdefiniertes Quellenanzeigefeld wird aktiviert, wenn KI-Antworten auf organisatorisches Wissen verweisen. Die Benutzeroberfläche bietet eine Steuerung zum Anzeigen von Quellen, ohne die Konversation zu verlassen.

Das Aktivieren der Quellenanzeige öffnet ein angrenzendes Panel. Benutzer sehen ihre Konversation auf der einen Seite und die Quelldetails auf der anderen, was eine gleichzeitige Überprüfung von Antworten und unterstützenden Materialien ermöglicht.

Quellen sind nach Dokumenten organisiert. Für jedes Dokument sehen Benutzer Metadaten – Datenbankstandort, Namespace, Titel – gefolgt von spezifischen Passagen, die zur Antwort beigetragen haben.

Das System zeigt spezifische abgerufene und der KI bereitgestellte Passagen (Nodes) an. Benutzer sehen genaue Textabschnitte, deren Kontext innerhalb der Quelldokumente und Relevanzbewertungen.

## Interaktive Exploration

Quellenverweise verlinken direkt zu vollständigen Dokumenten innerhalb des Wissensmanagement-Service. Benutzer können von einer abgerufenen Passage aus klicken, um das vollständige Dokument anzuzeigen.

Jede Passage beinhaltet den umgebenden Kontext wie Überschriftshierarchien und Dokumentstruktur. Dies hilft Benutzern zu verstehen, wo die Passage innerhalb ihrer Quelle positioniert ist.

Die Anzeige unterscheidet zwischen Quellen, die bei der Antwortgenerierung verwendet wurden, und Quellen, die zwar abgerufen, aber nicht ausgewählt wurden. Ein Umschalter steuert diese Unterscheidung. Dies hilft Benutzern, die Quellenauswahl der KI zu verstehen.

Wiederholte Interaktionen zeigen, welche Dokumente spezifische Themen behandeln, wo Wissenslücken bestehen und wie Informationen organisiert sind.

## Technische Implementierung

Während der Agenten-Ausführung erfasst die Plattform Retrieval-Events, die dokumentieren, auf welche Dokumente und Nodes zugegriffen wurde. Diese Events beinhalten Identifier, die Inhalte mit spezifischen Dokumenten in Wissensmanagement-Systemen verknüpfen. Wenn Benutzer die Quellenanzeige anfordern, fragt die Plattform diese Events ab, um die Ansicht zu erstellen.

Die Quellenanzeige koordiniert Daten aus dem Thread-Management (Konversationskontext), der Ereignisverfolgung (Retrieval-Aufzeichnungen) und dem Wissensmanagement (Dokumentdetails). Die Architektur wahrt Service-Grenzen, während sie diese Koordination ermöglicht.

Quellendaten werden bei Bedarf geladen, wenn Benutzer die Sichtbarkeit anfordern, anstatt für jede Nachricht vorab geladen zu werden. Benutzer erhalten bei Anforderung sofortigen Zugriff. Das System lädt keine Quellendaten für Konversationen, bei denen Benutzer keine Verifizierung benötigen.

Wenn das Retrieval zahlreiche Quellen zugreift, priorisiert die Anzeige die relevantesten Inhalte. Quellen, die direkt zu Antworten beitragen, erscheinen zuerst. Quellen mit geringerer Relevanz oder ungenutzte Quellen sind über erweiterte Ansichten oder Filter verfügbar.

## Was dies bietet

Wenn Benutzer KI-Antworten anhand von massgeblichen Quellen überprüfen können, steigt das Vertrauen. Die Verifizierung begegnet der "Black Box"-Problematik.

Für regulierte Industrien bietet die Quellenangabe Nachweisketten für KI-unterstützte Entscheidungen. Compliance-Audits können Empfehlungen zu genehmigten Materialien zurückverfolgen.

Wissensmanager validieren die Retrieval-Qualität durch Quellenangabe. Konsistent irrelevante Quellen oder Wissenslücken leiten Verbesserungen an – Hinzufügen von Dokumenten, Verfeinerung der Organisation oder Anpassung der Retrieval-Parameter.

Benutzer lernen, wie Wissensdatenbanken organisiert sind und welche Informationen existieren. Dies reduziert die Abhängigkeit von KI, da Benutzer direktes Wissen über organisationale Ressourcen entwickeln.

Für Entscheidungen mit hohen Einsätzen – regulatorische Compliance, finanzielle Verpflichtungen, betriebliche Änderungen – können Benutzer KI-Vorschläge vor der Umsetzung überprüfen.

## Feedback zum Wissensmanagement

Wenn Benutzer Quellen überprüfen und irrelevante Inhalte finden, fliesst dies in die Abstimmung des Retrieval-Systems zurück. Muster der Quellenprüfung, gefolgt von überarbeiteten Abfragen, deuten auf Qualitätsprobleme hin.

Wenn Konversationen keine geeigneten Quellen für häufige Anfragen aufdecken, signalisiert dies Lücken in der Wissensdatenbank. Organisationen priorisieren die Dokumentenbeschaffung basierend auf diesen Signalen.

Die Quellenangabe generiert Nutzungsdaten, die zeigen, welche Dokumente KI-Systeme am häufigsten referenzieren. Dies beeinflusst die Prioritäten der Kuration. Häufig aufgerufene Dokumente erfordern eine sorgfältige Pflege. Ungenutzte Dokumente können auf Organisationsprobleme hinweisen.

Wenn die Quellenangabe zeigt, dass Antworten auf veraltete Versionen zurückgreifen, erhalten Organisationen Signale zur Aktualisierung der Wissensdatenbanken.
```
