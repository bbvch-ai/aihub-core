---
title: Anfragen von betroffenen Personen (DSAR)
source_sha: d8c452a13b59ed46c1ae1deb9e2310fa5240d607b10556c9fc4059ba62ff5361
---

# Anfragen von betroffenen Personen

Betroffene Personen haben gemäss DSGVO (Artikel 15-21) und Schweizer revDSG (Artikel 25, 32) das Recht, ihre
personenbezogenen Daten einzusehen, zu berichtigen, zu löschen und zu kontrollieren. Dieser Abschnitt erläutert, welche
Unterstützung die Plattform für diese Rechte bietet.

## Antwortzeiten

Organisationen müssen auf Anfragen von betroffenen Personen gemäss DSGVO innerhalb eines Monats oder gemäss Schweizer
revDSG innerhalb von 30 Tagen antworten. Einige Anfragen können sofort bearbeitet werden, während andere eine manuelle
Datenerfassung erfordern.

## Zugriffsanfragen

Betroffene Personen können Kopien ihrer personenbezogenen Daten anfordern, einschliesslich der Verarbeitungszwecke,
Kategorien, Empfänger, Aufbewahrungsfristen und Datenquellen. Die Plattform speichert diese Informationen in
Benutzerprofilen, Konversationsverläufen und Audit-Logs. Organisationen überprüfen die Identität des Anfragenden, bevor
sie Daten bereitstellen.

::: warning Kompilierung von Chat-Daten für eine Anfrage
Standardmässig kann kein Administrator die Konversationen eines anderen Benutzers exportieren oder dessen hochgeladene
Dateien über die Chat-Oberfläche auflisten – diese Daten sind auf den jeweiligen Eigentümer beschränkt. Die Kompilierung
für eine Anfrage erfordert daher eine der folgenden Massnahmen: die betroffene Person exportiert ihre eigenen
Konversationen, die temporäre Verwendung der administrativen Übersteuerung (`OPENWEBUI_ENABLE_ADMIN_EXPORT` und
`OPENWEBUI_BYPASS_ADMIN_ACCESS_CONTROL`, siehe
[Übersicht der Chat-UI-Funktionen](../../10_chat_ui/1_feature_overview/)), oder direkten Datenbankzugriff. Planen Sie
dies bei der Festlegung interner Antwortzeitvorgaben ein.
:::

## Berichtigung

Betroffene Personen können die Berichtigung ungenauer Daten verlangen. Administratoren können Benutzerprofile über die
API der Plattform aktualisieren. Thread-Nachrichten und Audit-Logs bleiben unveränderlich, um Audit-Trails zu
gewährleisten.

## Löschung

Betroffene Personen können die Löschung von Daten verlangen, wenn diese nicht mehr erforderlich sind, die Einwilligung
widerrufen wird oder die Verarbeitung unrechtmässig ist. Ausnahmen gelten für rechtliche Verpflichtungen, Archivierung,
Forschung oder Rechtsansprüche. Die Plattform unterstützt das Entfernen von Benutzern aus Threads. Ephemere Daten werden
nach 30 Tagen automatisch gelöscht.

## Einschränkung der Verarbeitung

Betroffene Personen können die Aussetzung der Verarbeitung verlangen, während die Datenrichtigkeit überprüft oder
Einwände beurteilt werden. Administratoren können Konten über das Zugriffssteuerungssystem der Plattform sperren,
wodurch der Ressourcenzugriff verhindert und gleichzeitig die Daten erhalten bleiben.

## Datenübertragbarkeit

Betroffene Personen können ihre Daten in einem maschinenlesbaren Format anfordern. Dies gilt nur für Daten, die die
betroffene Person direkt bereitgestellt hat, wie Nachrichten und Uploads, nicht jedoch für KI-generierte Antworten,
Analysen oder abgeleitete Daten. Das Recht gilt, wenn die Verarbeitung auf Einwilligung oder Vertrag beruht und mittels
automatisierter Verfahren erfolgt.

## Widerspruch

Betroffene Personen können der Verarbeitung aufgrund berechtigter Interessen widersprechen. Organisationen widerrufen
Berechtigungen über die Zugriffssteuerung der Plattform, um die Verarbeitung einzustellen. Organisationen müssen
beurteilen, ob vorrangige berechtigte Interessen vorliegen.

## Verwandte Dokumentation

- [DSGVO-Konformität](../2_gdpr/)
- [Schweizer DSG](../3_dsg/)
- [Datenaufbewahrung](../1_data_retention/)

______________________________________________________________________

:::info Rechtlicher Hinweis
Dies ist eine technische Dokumentation, keine Rechtsberatung. Konsultieren Sie Ihren Datenschutzbeauftragten oder
Rechtsbeistand.
:::
