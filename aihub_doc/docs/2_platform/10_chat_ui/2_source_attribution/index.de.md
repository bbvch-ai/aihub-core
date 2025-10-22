---
title: Erweiterte Quellenattribution
index: 2
source_sha: 11ddc08db18ac079e2258508ce70b8a319d0f306aa39e506ddb17c4803190f45
---

# Erweiterte Quellenattribution

Eine entscheidende Erweiterung, die der Swiss AI Hub zur Standard-Chat-Erfahrung von Open WebUI hinzufügt, ist eine
umfassende Quellenattribution – eine transparente Sichtbarkeit, welche Wissensdokumente und Passagen genau die
KI-generierten Antworten beeinflusst haben. Diese Fähigkeit begegnet einer grundlegenden Herausforderung bezüglich
Vertrauen und Verifikation bei Enterprise-KI-Implementierungen.

## Die Herausforderung der Quellenattribution

Wenn KI-Systeme Antworten basierend auf organisationalen Wissensdatenbanken durch Retrieval-Augmented Generation (RAG)
generieren, sehen sich Benutzer mit einer grundlegenden Frage konfrontiert: „Woher weiß die KI das?“ Ohne Einblick in
die Quellmaterialien können Benutzer die Genauigkeit nicht überprüfen, die Relevanz beurteilen oder die Grundlage für
KI-Schlussfolgerungen verstehen. Diese Opazität untergräbt das Vertrauen und begrenzt die Akzeptanz von Enterprise-KI.

**Einschränkungen bei Standard-Chats**: Herkömmliche Chat-Oberflächen, einschließlich des nativen Open WebUI, bieten
Gesprächsinteraktionen ohne systematischen Einblick in die Abrufprozesse. Benutzer erhalten Antworten, aber es fehlt
ihnen die Einsicht, welche Dokumente, Passagen oder Wissensquellen diese Antworten beeinflusst haben. Für zwanglose
Konsumenteninteraktionen mag diese Opazität akzeptabel sein. Für die Entscheidungsfindung im Unternehmen ist sie
unzureichend.

**Compliance- und Verifikationsanforderungen**: Regulierte Industrien, Organisationen des öffentlichen Sektors und
qualitätskritische Bereiche erfordern Nachweisketten, die KI-generierte Inhalte unterstützen. Entscheidungsträger müssen
überprüfen, ob KI-Antworten mit maßgeblichen Quellen, aktuellen Richtlinien und genehmigten Informationen
übereinstimmen. Ohne Quellenattribution erfordert diese Verifikation manuelle Recherchen, die die Effizienzvorteile der
KI zunichtemachen.

**Qualitätssicherung des Wissens**: Organisationen, die Wissensdatenbanken pflegen, benötigen Feedback zur
Abrufqualität. Greifen Agenten auf geeignete Dokumente zu? Gibt es Wissenslücken bei häufigen Anfragen? Die
Quellenattribution bietet die notwendige Transparenz, um Qualitätsprobleme in der Wissensdatenbank zu identifizieren und
Verbesserungsbemühungen zu lenken.

## Integration der Quellenanzeige

Der Swiss AI Hub erweitert die Chat-Oberfläche durch ein benutzerdefiniertes Quellenanzeigefeld, das aktiviert wird,
wenn KI-Antworten auf organisatorisches Wissen verweisen.

**Kontextgesteuerte Anzeige**: Wenn Benutzer mit KI-Antworten interagieren, die durch Wissensabruf generiert werden,
bietet die Oberfläche die Möglichkeit, Quellen anzuzeigen. Eine klare, zugängliche Steuerung – typischerweise in die
Nachrichtensteuerungen integriert – ermöglicht es Benutzern, die Sichtbarkeit der Quellen anzufordern, ohne die
Konversation verlassen oder separate Anwendungen öffnen zu müssen.

**Zwei-Fenster-Darstellung**: Das Aktivieren der Quellenanzeige öffnet ein angrenzendes Panel innerhalb der
Chat-Oberfläche, wodurch der Konversationskontext erhalten bleibt, während Quelldetails präsentiert werden. Benutzer
sehen ihre Konversation im linken Bereich und detaillierte Quellinformationen im rechten Bereich, was eine gleichzeitige
Überprüfung von KI-Antworten und unterstützenden Materialien ermöglicht.

**Dokumentenzentrierte Organisation**: Quellen werden nach Dokumenten organisiert, anstatt eine undifferenzierte Liste
abgerufener Passagen anzuzeigen. Für jedes Quelldokument sehen Benutzer Dokumenten-Metadaten – Datenbankstandort,
Namespace, Dokumententitel – gefolgt von den spezifischen Passagen, die zur Antwort beigetragen haben. Diese
Organisation hilft Benutzern, die Breite und Art des Wissens zu verstehen, das die Antworten unterstützt.

**Granularität auf Passagen-Ebene**: Über die Dokumentenidentifikation hinaus zeigt das System spezifische Passagen
(Knoten) an, die abgerufen und der KI zur Verfügung gestellt wurden. Benutzer sehen die exakten Textabschnitte, ihren
Kontext innerhalb der Quelldokumente und Relevanzbewertungen, die die Abrufsicherheit angeben. Diese Granularität
ermöglicht eine präzise Überprüfung, wie die KI Quellinformationen interpretiert und angewendet hat.

## Interaktive Quellenexploration

Die Quellenattribution geht über die passive Anzeige hinaus und ermöglicht die interaktive Erkundung von
Wissensdatenbanken direkt aus Chat-Konversationen.

**Dokumentennavigation**: Quelleneinträge bieten eine direkte Navigation zu vollständigen Quelldokumenten innerhalb des
Wissensmanagementsystems. Benutzer können von einer abgerufenen Passage aus auf das vollständige Dokument klicken, um
den breiteren Kontext über die spezifische Passage hinaus zu verstehen, die die KI-Antwort beeinflusst hat.

**Visualisierung des Knotenkontexts**: Jede angezeigte Passage enthält den umgebenden Kontext – Überschriftshierarchien,
Dokumentstrukturindikatoren – um Benutzern zu helfen zu verstehen, wo sich die Passage innerhalb ihres Quelldokuments
befindet. Eine Passage aus einem Einleitungsabschnitt hat eine andere Gewichtung als eine aus detaillierten technischen
Spezifikationen.

**Aktive vs. ungenutzte Quellen**: Die Anzeige unterscheidet zwischen Quellen, die tatsächlich bei der
Antwortgenerierung verwendet wurden, und Quellen, die zwar abgerufen, aber nicht ausgewählt wurden. Diese Unterscheidung
– oft über einen Schalter gesteuert – hilft Benutzern, den Quellenauswahlprozess der KI zu verstehen und potenziell
relevante Informationen zu identifizieren, die nicht in die Antwort integriert wurden.

**Transparenz der Wissensdatenbank**: Durch die Quellenattribution entwickeln Benutzer Vertrautheit mit organisationalen
Wissensdatenbanken. Wiederholte Interaktionen zeigen, welche Dokumente bestimmte Themen behandeln, wo Wissenslücken
bestehen und wie Informationen organisiert sind – wodurch die Benutzerkenntnisse über spezifische KI-Interaktionen
hinaus beschleunigt werden.

## Technische Implementierung

Die Fähigkeit zur Quellenattribution resultiert aus einer ausgeklügelten Integration zwischen Chat-Oberfläche,
Wissensmanagementsystemen und der Infrastruktur zur Agentenausführung.

**Ereigniserfassung und -korrelation**: Während der Agentenausführung erfasst die Plattform detaillierte
Abrufereignisse, die dokumentieren, auf welche Dokumente und Knoten zugegriffen wurde. Diese Ereignisse enthalten
Identifikatoren, die abgerufene Inhalte mit spezifischen Dokumenten in Wissensmanagementsystemen verknüpfen. Wenn
Benutzer die Quellenanzeige anfordern, fragt die Plattform diese Ereignisse ab, um die Quellenansicht zu erstellen.

**Dienstübergreifende Datenintegration**: Die Quellenanzeige erfordert die Koordination von Daten aus mehreren Diensten
– Thread-Management (für den Konversationskontext), Ereignisverfolgung (für Abrufprotokolle) und Wissensmanagement (für
Dokumentendetails). Die Integrationsarchitektur ermöglicht diese dienstübergreifende Koordination, während Dienstgrenzen
und Leistung beibehalten werden.

**Echtzeit-Abruf**: Quellendaten werden bei Bedarf geladen, wenn Benutzer die Sichtbarkeit anfordern, anstatt für jede
Nachricht vorab geladen zu werden. Diese Optimierung gleicht die Reaktionsfähigkeit (Benutzer erhalten bei Bedarf
sofortigen Quellenzugriff) mit der Effizienz (das System lädt keine Quelldaten für Konversationen, bei denen Benutzer
keine Verifikation benötigen) aus.

**Filterung und Relevanzranking**: Wenn Abrufoperationen auf zahlreiche Quellen zugreifen, priorisiert die Anzeige die
relevantesten Inhalte. Benutzer sehen zuerst Quellen, die direkt zu den Antworten beitragen, wobei Quellen mit
geringerer Relevanz oder ungenutzte Quellen über erweiterte Ansichten oder Filtersteuerungen verfügbar sind.

## Geschäftswert

Erweiterte Quellenattribution liefert spezifische Geschäftsvorteile für Enterprise-KI-Implementierungen.

**Vertrauensbildung**: Wenn Benutzer KI-Antworten anhand maßgeblicher Quellen überprüfen können, steigt das Vertrauen in
KI-Systeme. Diese Verifikationsfähigkeit beschleunigt die Akzeptanz, indem sie das „Black Box“-Problem anspricht, das
oft die Einführung von Enterprise-KI behindert.

**Regulatorische Compliance**: Für Organisationen in regulierten Branchen bietet die Quellenattribution Nachweisketten,
die KI-unterstützte Entscheidungen untermauern. Compliance-Audits können spezifische Empfehlungen oder
Schlussfolgerungen auf genehmigte Quellmaterialien zurückführen und so die regulatorischen Dokumentationsanforderungen
erfüllen.

**Qualitätssicherung**: Wissensmanager nutzen die Quellenattribution, um die Abrufqualität zu validieren. Wenn Benutzer
konsistent irrelevante Quellen oder Wissenslücken finden, leitet dieses Feedback die Verbesserung der Wissensdatenbank –
das Hinzufügen fehlender Dokumente, die Verbesserung der Organisation oder die Verfeinerung der Abrufparameter.

**Benutzerschulung**: Die Quellenattribution erfüllt eine Bildungsfunktion, indem sie Benutzern hilft zu verstehen, wie
Wissensdatenbanken organisiert sind und welche Informationen verfügbar sind. Diese Schulung reduziert die Abhängigkeit
von KI-Vermittlung, da Benutzer ein direktes Wissen über organisationale Informationsressourcen entwickeln.

**Vertrauen bei Entscheidungen mit hohen Einsätzen**: Bei Entscheidungen mit erheblichen Konsequenzen – regulatorische
Compliance, finanzielle Verpflichtungen, betriebliche Änderungen – können Benutzer KI-Vorschläge gründlich überprüfen,
bevor sie handeln, wodurch die Effizienz der KI mit menschlichem Urteilsvermögen und Verifikation kombiniert wird.

## Integration in den Wissenslebenszyklus

Die Quellenattribution integriert sich in den umfassenderen Wissensmanagement-Lebenszyklus der Plattform und schafft
Feedback-Schleifen, die die Wissensqualität im Laufe der Zeit verbessern.

**Feedback zur Abrufqualität**: Wenn Benutzer Quellen prüfen und irrelevante Inhalte finden, kann dieses implizite
Feedback zur Abstimmung des Abrufsystems verwendet werden. Muster der Quellenprüfung, gefolgt von überarbeiteten
Anfragen, weisen auf Abrufqualitätsprobleme hin, die Aufmerksamkeit erfordern.

**Identifikation von Wissenslücken**: Wenn Konversationen keine geeigneten Quellen für häufige Anfragen aufdecken,
deutet dies auf Lücken in der Wissensdatenbank hin. Organisationen können die Beschaffung oder Erstellung von Dokumenten
priorisieren, basierend auf der Quellenattribution, die ungedeckte Informationsbedürfnisse aufzeigt.

**Dokumentennutzungsanalyse**: Die Quellenattribution generiert Nutzungsdaten, die zeigen, welche
Wissensdatenbank-Dokumente von KI-Systemen am häufigsten referenziert werden. Diese Analyse informiert über Prioritäten
der Wissenskuration – häufig genutzte Dokumente verdienen sorgfältige Wartung und Aktualisierung, während ungenutzte
Dokumente auf Organisations- oder Relevanzprobleme hinweisen können.

**Versions- und Aktualitätsüberwachung**: Wenn die Quellenattribution zeigt, dass KI-Antworten auf veralteten
Dokumentversionen basieren, erhalten Organisationen Signale zur Aktualisierung ihrer Wissensdatenbanken. Diese
Überwachung unterstützt die automatisierten Wissenssynchronisationsfunktionen der Plattform.

## Wettbewerbsdifferenzierung

Die Quellenattribution stellt eine signifikante Erweiterung über die Standardfunktionen von Chat-Oberflächen,
einschließlich der nativen Open WebUI-Funktionalität, hinaus dar.

**Über Standard-Abruf-Indikatoren hinaus**: Während einige Chat-Systeme minimale Abruf-Indikatoren – Fußnoten oder
Referenznummern – bereitstellen, bietet die umfassende Quellenanzeige des Swiss AI Hub eine Organisation auf
Dokumentenebene, Granularität auf Passagen-Ebene, interaktive Exploration und Wissensmanagement-Integration. Diese Tiefe
der Attribution übertrifft das, was eigenständige Chat-Oberflächen typischerweise bieten.

**Enterprise-taugliche Verifikation**: Die Funktion erkennt an, dass KI-Implementierungen in Unternehmen und im
öffentlichen Sektor Verifikationsanforderungen haben, die über die von Verbraucheranwendungen hinausgehen. Die
Quellenattribution schlägt eine Brücke zwischen der Effizienz konversationeller KI und der Strenge der
Entscheidungsfindung in Unternehmen.

**Wissensmanagement-Integration**: Die Quellenattribution ist keine isolierte Funktion, sondern eine integrierte
Fähigkeit, die Chat-Interaktionen mit dem umfassenden Wissensmanagementsystem der Plattform verbindet. Diese Integration
ermöglicht Workflows, die über die Verifikation hinausgehen – Benutzer können von Chat-Antworten zur Wissenserkundung,
Dokumentenbearbeitung und Wissensdatenbank-Administration navigieren.

Diese Erweiterung demonstriert den Ansatz des Swiss AI Hub zur Open-Source-Integration: bewährte Grundlagen übernehmen
(Open WebUI für Chat), dann mit unternehmensspezifischen Funktionen (Quellenattribution) erweitern, die
Geschäftsanforderungen jenseits von Consumer-Chat-Anwendungen adressieren. Organisationen profitieren sowohl von der
Reichhaltigkeit gemeinschaftlich entwickelter Chat-Oberflächen als auch von der Strenge, die für
Enterprise-Implementierungen erforderlich ist.
