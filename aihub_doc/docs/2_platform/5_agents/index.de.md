---
title: Agenten
source_sha: "1d0a566a2f45f51f93bc6d7467f5d746540f7ee18a679849fb429fb53b1d5452"
---

# Agenten

Im Zentrum des Swiss AI Hubs stehen **Agenten**: spezialisierte KI-Assistenten, die darauf ausgelegt sind, spezifische Aufgaben innerhalb eines strukturierten und zuverlässigen Rahmens auszuführen. Im Gegensatz zu offenen Chatbots agieren unsere Agenten wie Expertenkollegen. Sie interagieren mit ihnen über die Chat-Oberfläche, und sie folgen klar definierten Workflows, um Ihnen bei der Analyse von Dokumenten, der Beantwortung von Fragen oder der Durchführung von Geschäftsprozessen zu helfen.

Dieser strukturierte Ansatz ist eine zentrale Designentscheidung. Er stellt sicher, dass Agenten nicht nur intelligent, sondern auch vorhersehbar, transparent und auditierbar sind – Eigenschaften, die für den Einsatz in Unternehmen und im öffentlichen Sektor unerlässlich sind.

## Was ist ein Agent?

Im Swiss AI Hub ist ein Agent ein KI-gestützter Assistent, mit dem Sie in einem Chat interagieren. Jeder Agent ist so konfiguriert, dass er eine spezifische Reihe von Aufgaben mithilfe eines vordefinierten Workflows bearbeitet.

Stellen Sie sich sie als digitale Spezialisten vor:
- Ein **HR-Richtlinien-Agent** kann Fragen zu den Urlaubsrichtlinien Ihres Unternehmens beantworten, indem er das offizielle Mitarbeiterhandbuch konsultiert.
- Ein **Finanzanalyst-Agent** kann Ihnen dabei helfen, die Verkaufsdaten des letzten Quartals aus einem spezifischen Bericht abzufragen.
- Ein **Projekt-Support-Agent** kann die neuesten Statusaktualisierungen aus einer Sammlung von Projektdokumenten zusammenfassen.

Diese Agenten verbinden die Leistungsfähigkeit großer Sprachmodelle (LLMs) für das natürliche Sprachverständnis mit der Zuverlässigkeit eines strukturierten Prozesses.

## Wie Agenten funktionieren: Der Workflow-Vorteil

Das Verhalten eines Agenten wird durch einen **Workflow** gesteuert, der eine vordefinierte Abfolge von Schritten darstellt. Dies ist der entscheidende Unterschied zwischen unseren Agenten und einer Allzweck-KI wie ChatGPT.

Ein typischer Workflow könnte so aussehen:

1.  **Benutzeranfrage verstehen**: Der Agent verwendet ein LLM, um Ihre Frage zu interpretieren.
2.  **Relevante Informationen abrufen**: Falls erforderlich, führt der Agent eine semantische Suche in einer bestimmten Wissensdatenbank (z. B. einem spezifischen SharePoint-Ordner) durch, um relevante Dokumente zu finden. Dies wird als Retrieval-Augmented Generation (RAG) bezeichnet.
3.  **Antwort synthetisieren**: Der Agent kombiniert Ihre ursprüngliche Frage mit den abgerufenen Informationen und verwendet ein LLM, um eine klare, genaue und hilfreiche Antwort zu generieren.
4.  **Quellen angeben**: Die endgültige Antwort enthält direkte Verweise auf die Quelldokumente, sodass Sie die Informationen jederzeit überprüfen können.

Dieser Workflow-basierte Ansatz bietet mehrere wichtige Vorteile:
-   **Transparenz**: Sie können die Schritte sehen, die der Agent unternommen hat, um zu einer Antwort zu gelangen, einschließlich der Dokumente, die er konsultiert hat. Dies eliminiert das „Black-Box“-Problem und schafft Vertrauen.
-   **Zuverlässigkeit**: Durch die Beschränkung des Agenten auf einen spezifischen Workflow und eine Wissensdatenbank wird das Risiko von „Halluzinationen“ oder sachlich falschen Antworten drastisch reduziert.
-   **Kontrolle**: Administratoren und Entwickler legen fest, was ein Agent tun kann und was nicht. Ein Agent kann nicht entscheiden, auf Daten zuzugreifen, die er nicht sollte, oder Aktionen außerhalb seines definierten Workflows auszuführen.

## Agenten in Aktion: Ein praktisches Beispiel

Stellen Sie sich vor, Sie fragen den „IT-Support-Agenten“: *„Wie richte ich das neue VPN auf meinem Laptop ein?“*

Anstatt eine allgemeine Antwort aus dem Internet zu geben, führt der Agent seinen Workflow aus:

1.  Er identifiziert die Schlüsselwörter „VPN“ und „Einrichtung“.
2.  Er durchsucht die interne „IT-Wissensdatenbank“ des Unternehmens nach Dokumenten, die diesen Begriffen entsprechen.
3.  Er findet die offizielle, aktuelle Anleitung mit dem Titel „VPN_Setup_Guide_v3.pdf“.
4.  Er liest die relevanten Abschnitte des PDF.
5.  Er gibt Ihnen eine Schritt-für-Schritt-Zusammenfassung, die *ausschließlich* auf diesem Dokument basiert, und fügt einen direkten Link zum PDF als Referenz bei.

Das Ergebnis ist eine vertrauenswürdige, relevante und überprüfbare Antwort. Dies ist die Stärke der Kombination von KI-Sprachfähigkeiten mit strukturierten, auditierbaren Workflows.

## Human-in-the-Loop: Kollaboration, nicht nur Automatisierung

Manche Aufgaben erfordern menschliches Urteilsvermögen. Unsere Agenten-Workflows sind darauf ausgelegt, menschliche Aufsicht nahtlos zu integrieren. Ein Agent kann so konfiguriert werden, dass er seinen Prozess pausiert und auf Ihre Genehmigung wartet, bevor er einen kritischen Schritt unternimmt. Zum Beispiel könnte ein Agent einen Entwurf einer Antwort auf eine Kundenanfrage vorbereiten, aber warten, bis ein Support-Teammitglied diesen überprüft und genehmigt, bevor er ihn versendet.

Diese „Human-in-the-Loop“-Fähigkeit macht unsere Agenten zu mächtigen Assistenten für komplexe Prozesse, die es Ihnen ermöglicht, die Routineanteile einer Aufgabe zu automatisieren, während Sie die volle Kontrolle über die endgültige Entscheidung behalten.
