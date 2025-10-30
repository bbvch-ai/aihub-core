---
title: Chatten Sie mit dem Wissen Ihres Unternehmens
source_sha: 66544141a5dc306b4e7e58dcb6e5fc7226b2979127af8dddb6203b26baaa55c2
---

# Chatten Sie mit dem Wissen Ihres Unternehmens

Der Swiss AI Hub zeigt Benutzern, welche Wissensdokumente und Textpassagen die KI-Antworten informierten. Diese
Transparenz hilft Benutzern, die Genauigkeit zu überprüfen und die Grundlage für KI-Schlussfolgerungen zu verstehen.

## Warum das wichtig ist

Wenn KI-Systeme Retrieval-Augmented Generation (RAG) mit organisatorischen Wissensdatenbanken verwenden, müssen Benutzer
überprüfen, woher die Informationen stammen. Standard-Chat-Oberflächen, einschließlich des nativen Open WebUI, zeigen
nicht systematisch an, welche Dokumente oder Passagen die Antworten informierten.

Regulierte Branchen und qualitätskritische Bereiche erfordern Nachweisketten für KI-generierte Inhalte.
Entscheidungsträger müssen überprüfen, ob die Antworten mit maßgeblichen Quellen und aktuellen Richtlinien
übereinstimmen. Ohne Quellenangabe erfordert die Verifizierung eine manuelle Recherche.

Organisationen, die Wissensdatenbanken pflegen, benötigen Feedback zur Qualität des Abrufs. Die Quellenangabe zeigt, ob
Agenten auf geeignete Dokumente zugreifen und deckt Wissenslücken bei häufigen Anfragen auf.

## So funktioniert es

Ein benutzerdefiniertes Quellenanzeigefeld wird aktiviert, wenn KI-Antworten auf organisatorisches Wissen verweisen. Die
Oberfläche bietet eine Steuerung zum Anzeigen von Quellen, ohne die Konversation zu verlassen.

Das Aktivieren der Quellenanzeige öffnet ein angrenzendes Panel. Benutzer sehen ihre Konversation auf der einen Seite
und die Quelldetails auf der anderen, was eine gleichzeitige Überprüfung von Antworten und unterstützenden Materialien
ermöglicht.

Quellen werden nach Dokumenten organisiert. Für jedes Dokument sehen Benutzer Metadaten – Datenbankstandort, Namespace,
Titel – gefolgt von spezifischen Passagen, die zur Antwort beigetragen haben.

Das System zeigt spezifische abgerufene und der KI zur Verfügung gestellte Passagen (Knotenpunkte) an. Benutzer sehen
genaue Textabschnitte, deren Kontext innerhalb der Quelldokumente und Relevanzbewertungen.

## Interaktive Erkundung

Quelleneinträge verlinken direkt zu vollständigen Dokumenten innerhalb des Wissensmanagementdienstes. Benutzer können
von einer abgerufenen Passage aus auf das vollständige Dokument klicken.

Jede Passage enthält den umgebenden Kontext wie Überschriftenhierarchien und Dokumentstruktur. Dies hilft Benutzern zu
verstehen, wo die Passage in ihrer Quelle verortet ist.

Die Anzeige unterscheidet zwischen Quellen, die bei der Antwortgenerierung verwendet wurden, und Quellen, die zwar
abgerufen, aber nicht ausgewählt wurden. Ein Umschalter steuert diese Unterscheidung. Dies hilft Benutzern, die
Quellenauswahl der KI zu verstehen.

Wiederholte Interaktionen zeigen, welche Dokumente spezifische Themen behandeln, wo Wissenslücken bestehen und wie
Informationen organisiert sind.

## Technische Implementierung

Während der Agentenausführung erfasst die Plattform Abrufereignisse, die dokumentieren, auf welche Dokumente und
Knotenpunkte zugegriffen wurde. Diese Ereignisse enthalten Kennungen, die Inhalte mit spezifischen Dokumenten in
Wissensmanagementsystemen verknüpfen. Wenn Benutzer die Quellenanzeige anfordern, fragt die Plattform diese Ereignisse
ab, um die Ansicht zu erstellen.

Die Quellenanzeige koordiniert Daten aus dem Thread-Management (Konversationskontext), der Ereignisverfolgung
(Abrufaufzeichnungen) und dem Wissensmanagement (Dokumentendetails). Die Architektur wahrt Dienstgrenzen, während sie
diese Koordination ermöglicht.

Quelldaten werden bei Bedarf geladen, wenn Benutzer die Sichtbarkeit anfordern, anstatt für jede Nachricht vorab geladen
zu werden. Benutzer erhalten bei Anfrage sofortigen Zugriff. Das System lädt keine Quelldaten für Konversationen, in
denen Benutzer keine Verifizierung benötigen.

Wenn der Abruf auf zahlreiche Quellen zugreift, priorisiert die Anzeige die relevantesten Inhalte. Quellen, die direkt
zu den Antworten beitragen, erscheinen zuerst. Quellen mit geringerer Relevanz oder ungenutzte Quellen sind über
erweiterte Ansichten oder Filter verfügbar.

## Was dies bietet

Wenn Benutzer KI-Antworten anhand maßgeblicher Quellen überprüfen können, steigt das Vertrauen. Die Verifizierung
begegnet der „Black-Box“-Problematik.

Für regulierte Branchen bietet die Quellenangabe Nachweisketten für KI-gestützte Entscheidungen. Compliance-Audits
können Empfehlungen auf genehmigte Materialien zurückführen.

Wissensmanager validieren die Qualität des Abrufs durch Quellenangabe. Konsistent irrelevante Quellen oder Wissenslücken
leiten Verbesserungen an – Hinzufügen von Dokumenten, Verfeinern der Organisation oder Anpassen der Abrufparameter.

Benutzer lernen, wie Wissensdatenbanken organisiert sind und welche Informationen existieren. Dies reduziert die
Abhängigkeit von KI, da Benutzer direktes Wissen über die Ressourcen der Organisation entwickeln.

Bei wichtigen Entscheidungen – wie der Einhaltung von Vorschriften, finanziellen Verpflichtungen oder betrieblichen
Änderungen – können Benutzer KI-Vorschläge überprüfen, bevor sie handeln.

## Feedback zum Wissensmanagement

Wenn Benutzer Quellen prüfen und irrelevante Inhalte finden, fließt dies in die Feinabstimmung des Abrufsystems zurück.
Muster der Quellenprüfung, gefolgt von überarbeiteten Anfragen, weisen auf Qualitätsprobleme hin.

Wenn Konversationen keine geeigneten Quellen für häufige Anfragen aufzeigen, deutet dies auf Lücken in der
Wissensdatenbank hin. Organisationen priorisieren die Dokumentenbeschaffung basierend auf diesen Signalen.

Die Quellenangabe generiert Nutzungsdaten, die zeigen, welche Dokumente KI-Systeme am häufigsten referenzieren. Dies
beeinflusst die Prioritäten der Kuratierung. Häufig aufgerufene Dokumente erfordern eine sorgfältige Pflege. Ungenutzte
Dokumente können auf Organisationsprobleme hinweisen.

Wenn die Quellenangabe zeigt, dass Antworten auf veraltete Versionen zurückgreifen, erhalten Organisationen Signale zur
Aktualisierung ihrer Wissensdatenbanken.
