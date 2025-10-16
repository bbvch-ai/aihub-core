---
title: Agenten
index: 5
source_sha: "4e8f7b68caa8a48ca3786003731e794bef211757061453783599d0984343ea3d"
---

# Agenten

Im Zentrum des Swiss AI Hub stehen **Agenten**: spezialisierte KI-Assistenten, die darauf ausgelegt sind, spezifische Aufgaben innerhalb eines strukturierten und zuverlässigen Rahmens auszuführen. Im Gegensatz zu offenen Chatbots agieren unsere Agenten wie erfahrene Kollegen. Sie interagieren mit ihnen über die Chat-Oberfläche, und sie folgen klar definierten Workflows, um Ihnen bei der Analyse von Dokumenten, der Beantwortung von Fragen oder der Abwicklung von Geschäftsprozessen zu helfen.

Dieser strukturierte Ansatz ist eine zentrale Designentscheidung. Er gewährleistet, dass Agenten nicht nur intelligent, sondern auch vorhersehbar, transparent und auditierbar sind – Eigenschaften, die für den Einsatz in Unternehmen und im öffentlichen Sektor unerlässlich sind.

## Was ist ein Agent?

Im Swiss AI Hub ist ein Agent ein KI-gestützter Assistent, mit dem Sie im Chat interagieren. Jeder Agent ist so konfiguriert, dass er eine bestimmte Reihe von Aufgaben mithilfe eines vordefinierten Workflows bearbeitet.

Stellen Sie sich diese als digitale Spezialisten vor:
- Ein **HR-Richtlinien-Agent** kann Fragen zu den Urlaubsrichtlinien Ihres Unternehmens beantworten, indem er das offizielle Mitarbeiterhandbuch konsultiert.
- Ein **Finanzanalysten-Agent** kann Ihnen helfen, die Verkaufsdaten des letzten Quartals aus einem bestimmten Bericht abzufragen.
- Ein **Projektunterstützungs-Agent** kann die neuesten Statusaktualisierungen aus einer Sammlung von Projektdokumenten zusammenfassen.

Diese Agenten verbinden die Leistungsfähigkeit großer Sprachmodelle (LLMs) für das natürliche Sprachverständnis mit der Zuverlässigkeit eines strukturierten Prozesses.

## Wie Agenten funktionieren: Der Workflow-Vorteil

Das Verhalten eines Agenten wird durch einen **Workflow** gesteuert, eine vordefinierte Abfolge von Schritten. Dies ist der entscheidende Unterschied zwischen unseren Agenten und einer Allzweck-KI wie ChatGPT.

Ein typischer Workflow könnte wie folgt aussehen:

1.  **Benutzeranfrage verstehen**: Der Agent nutzt ein LLM, um Ihre Frage zu interpretieren.
2.  **Relevante Informationen abrufen**: Falls erforderlich, führt der Agent eine semantische Suche in einer bestimmten Wissensdatenbank (z.B. einem spezifischen SharePoint-Ordner) durch, um relevante Dokumente zu finden. Dies wird als Retrieval-Augmented Generation (RAG) bezeichnet.
3.  **Antwort synthetisieren**: Der Agent kombiniert Ihre ursprüngliche Frage mit den abgerufenen Informationen und verwendet ein LLM, um eine klare, genaue und hilfreiche Antwort zu generieren.
4.  **Quellen angeben**: Die endgültige Antwort enthält direkte Verweise auf die Quelldokumente, sodass Sie die Informationen jederzeit überprüfen können.

Dieser Workflow-basierte Ansatz bietet mehrere entscheidende Vorteile:
-   **Transparenz**: Sie können die Schritte nachvollziehen, die der Agent unternommen hat, um zu einer Antwort zu gelangen, einschließlich der konsultierten Dokumente. Dies eliminiert das „Black-Box“-Problem und schafft Vertrauen.
-   **Zuverlässigkeit**: Indem der Agent auf einen spezifischen Workflow und eine Wissensdatenbank beschränkt wird, wird das Risiko von „Halluzinationen“ oder sachlich falschen Antworten drastisch reduziert.
-   **Kontrolle**: Administratoren und Entwickler definieren, was ein Agent tun kann und was nicht. Ein Agent kann nicht selbstständig entscheiden, auf Daten zuzugreifen, die er nicht sollte, oder Aktionen außerhalb seines definierten Workflows auszuführen.

## Agenten in Aktion: Ein praktisches Beispiel

Stellen Sie sich vor, Sie fragen den „IT-Support-Agenten“: *„Wie richte ich das neue VPN auf meinem Laptop ein?“*

Anstatt eine allgemeine Antwort aus dem Internet zu geben, führt der Agent seinen Workflow aus:

1.  Er identifiziert die Schlüsselwörter „VPN“ und „Einrichtung“.
2.  Er durchsucht die interne „IT-Wissensdatenbank“ des Unternehmens nach Dokumenten, die diesen Begriffen entsprechen.
3.  Er findet die offizielle, aktuelle Anleitung mit dem Titel „VPN_Setup_Guide_v3.pdf“.
4.  Er liest die relevanten Abschnitte des PDFs.
5.  Er liefert Ihnen eine schrittweise Zusammenfassung, die sich *ausschließlich* auf dieses Dokument stützt, und fügt einen direkten Link zum PDF als Referenz bei.

Das Ergebnis ist eine vertrauenswürdige, relevante und überprüfbare Antwort. Dies ist die Stärke der Kombination von KI-Sprachfähigkeiten mit strukturierten, auditierbaren Workflows.

## Human-in-the-Loop: Kollaboration, nicht nur Automation

Manche Aufgaben erfordern menschliches Urteilsvermögen. Unsere Agenten-Workflows sind darauf ausgelegt, menschliche Aufsicht nahtlos zu integrieren. Ein Agent kann so konfiguriert werden, dass er seinen Prozess unterbricht und auf Ihre Genehmigung wartet, bevor er einen kritischen Schritt ausführt. Ein Agent könnte beispielsweise einen Antwortentwurf für eine Kundenanfrage vorbereiten, aber warten, bis ein Support-Mitarbeiter ihn überprüft und genehmigt, bevor er gesendet wird.

Diese „Human-in-the-Loop“-Fähigkeit macht unsere Agenten zu leistungsstarken Assistenten für komplexe Prozesse, indem sie es Ihnen ermöglicht, die Routineanteile einer Aufgabe zu automatisieren, während Sie die volle Kontrolle über die endgültige Entscheidung behalten.
