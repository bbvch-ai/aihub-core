---
title: Anonymisierer
description: Ersetzt Personendaten in einem Text durch Platzhalter, damit Sie ihn in jedem Werkzeug verwenden können, und setzt die Originalwerte wieder in die Antwort ein. Kein KI-Modell sieht Ihren Text.
source_sha: 5acfa24267723577a806532baf0443ad16f5fddf651be13b6e2d25ebd41d2c75
---

# Anonymisierer

Mit dem **Anonymisierer** anonymisieren Benutzer einen Text selbst. Sie senden ihm einen Text und erhalten ihn zurück,
in dem Namen, Adressen, AHV-Nummern und andere Personendaten durch Platzhalter wie `<PERSON_1>` ersetzt sind. Diesen
Text können sie in jeden anderen Agenten, Chat oder ein externes Werkzeug einfügen, die Antwort anschliessend in
denselben Chat zurückkopieren und erhalten sie mit den Originalwerten.

Er ruft kein Sprachmodell auf. Der Text geht nur an den Presidio-Analyzer der eigenen Installation, denselben, den das
Gateway für die [Datenanonymisierung](../../13_language_models/2_anonymization/) verwendet. Nichts, was der
Anonymisierer verarbeitet, verlässt die Installation.

## Was Benutzer sehen

1. Ein Benutzer sendet: "Bitte schreiben Sie Reto Wyss, Seefeldstrasse 18, 8008 Zürich, wegen seiner AHV
   756.1234.5678.97."
2. Der Anonymisierer antwortet mit dem Text in einem kopierbaren Block: "Bitte schreiben Sie `<PERSON_1>`,
   `<CH_ADDRESS_2>`, wegen seiner AHV `<NATIONAL_ID_3>`."
3. Der Benutzer fügt diesen Text in ein anderes Werkzeug ein und erhält eine Antwort wie "Sehr geehrter `<PERSON_1>`,
   …".
4. Der Benutzer fügt die Antwort in denselben Anonymisierer-Chat ein und erhält "Sehr geehrter Reto Wyss, …".

Der Chat entscheidet die Richtung pro Nachricht: Eine Nachricht mit Platzhaltern, die dieser Chat vergeben hat, wird
wiederhergestellt, alles andere wird anonymisiert.

- **Stabile Platzhalter.** Ein Wert behält seinen Platzhalter im ganzen Chat, Reto Wyss ist also in jeder Nachricht
  `<PERSON_1>`, und die Wiederherstellung funktioniert beliebig viele Nachrichten später.
- **Ein Chat, eine Zuordnung.** Ein Chat stellt nur die Platzhalter wieder her, die er selbst vergeben hat. Ein neuer
  Chat kann die Platzhalter eines anderen Chats nicht wiederherstellen.
- **Fremde Platzhalter werden genannt.** Platzhalter, die der Chat nie vergeben hat, bleiben unverändert, und die
  Antwort listet sie auf.
- **Kein Titel aus dem Inhalt.** Der Chat heisst "Anonymisierter Text", damit die Chatliste nie die Personendaten zeigt.

## Was er bewusst weglässt

| Funktion                                                  | Anonymisierer |
| --------------------------------------------------------- | :-----------: |
| Aufrufe eines Sprachmodells (Antwort, Titel, Folgefragen) |      ❌       |
| Benutzer- oder Organisationsgedächtnis                    |      ❌       |
| Angehängte Dateien und Bilder                             |      ❌       |
| Wissensreferenzen (`#`)                                   |      ❌       |

Anonymisiert wird nur der Text der Nachricht. Um automatisch zu anonymisieren, was ein Agent an sein Modell sendet,
verwenden Sie stattdessen die Checkbox **Personendaten anonymisieren** in seinem Profil (siehe
[Ein Agentenprofil anonymisieren](../../13_language_models/2_anonymization/#ein-agentenprofil-anonymisieren)).

## Konfigurationsreferenz

Ein Profil braucht nur seine Identität: ID, Name, Beschreibung und Icon. Was als Personendaten gilt, ist dieselbe Liste,
die das Gateway verwendet, ein von Hand anonymisierter Text und eine vom Gateway anonymisierte Anfrage maskieren also
dasselbe.

Die Installation betreibt den Blueprint als Dienst `anonymiser_agent`, der den Analyzer über das Netzwerk
`pii-detection` mit `PRESIDIO_ANALYZER_API_BASE` und `PRESIDIO_ANALYZER_API_KEY` erreicht. Er hat keinen Zugang zu
LiteLLM.

## Grenzen

- Die Zuordnung wird mit dem Agentenzustand des Chats gespeichert und enthält damit Personendaten, wie der Chatverlauf.
- Das andere Werkzeug muss die Platzhalter genau so zurückschreiben, wie es sie erhalten hat. Ein Werkzeug, das sie
  verändert (`<Person_1>`), lässt sie im wiederhergestellten Text stehen.
- Die Erkennung hat dieselben Grenzen wie die des Gateways; siehe
  [Was erkannt wird](../../13_language_models/2_anonymization/#was-erkannt-wird).
