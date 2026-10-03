---
title: My Files
source_sha: 2fd161970a972152ab36182516b9f76063077781974e1d20ad151d578a788e97
---

# My Files

**My Files** ist Ihr eigener Dateibereich: jede Datei, die Sie in einem Agent-Chat anhängen, jede Datei, die ein Agent
für Sie erstellt, und alles, was Sie selbst hochladen, an einem Ort. Sie können Dateien öffnen, herunterladen,
hochladen, umbenennen, in Ordner verschieben und löschen, und Agents können sie lesen, wenn Sie es erlauben.

Die Dateien liegen in Ihrem Home in der Code-Sandbox, am selben Ort, an dem der
[Universal Agent](../../5_agents/13_universal_agent/) Code ausführt und das Terminal von OpenWebUI arbeitet. Niemand
sonst sieht sie.

## Wo Sie es finden

- **Eigenständig**: Öffnen Sie **My Files** im App-Menü.
- **Neben einem Chat**: Klicken Sie auf das Ordner-Symbol unter der Antwort eines Agents. My Files öffnet sich neben dem
  Chat, im Ordner dieses Chats.

## Wie es organisiert ist

- **`conversations/`** enthält einen Ordner pro Agent-Chat, angezeigt mit dem Titel des Chats. Jede Datei, die Sie in
  diesem Chat anhängen, landet dort, ebenso Dateien, die ein Agent darin erstellt hat.
- Alles andere organisieren Sie selbst: Erstellen Sie Ordner und verschieben Sie Dateien hinein.

Dateien, deren Name mit einem Punkt beginnt, sind ausgeblendet; sie gehören zur Sandbox und ihren Tools.

## Was Sie tun können

| Aktion               | So geht's                                                                                        |
| -------------------- | ------------------------------------------------------------------------------------------------ |
| Ordner öffnen        | Klicken Sie darauf; der Pfad über der Liste führt Sie zurück.                                    |
| Datei in der Vorschau anzeigen | Klicken Sie darauf. Text, Bilder und PDFs werden neben der Liste angezeigt.            |
| Herunterladen        | Das Download-Symbol. Jede Datei wird genau so heruntergeladen, wie sie gespeichert ist, auch Office-Dokumente. |
| Hochladen            | **Upload**, oder ziehen Sie Dateien auf die Liste. Eine Datei mit demselben Namen wird ersetzt.  |
| Neuer Ordner         | **New folder**.                                                                                  |
| Umbenennen           | Das Stift-Symbol.                                                                                |
| Verschieben          | Das Ordner-Symbol: in einen Ordner im aktuellen Ordner oder eine Ebene nach oben.                |
| Löschen              | Das Papierkorb-Symbol. Ein Ordner wird mit allem darin gelöscht.                                 |

Änderungen wirken sofort: Code, den ein Agent anschließend ausführt, sieht sie.

## Einen Agent Ihre Dateien lesen lassen

Schalten Sie in einem Chat mit dem Universal Agent **My Files** in den Schaltern des Chats ein. Der Agent kann dann Ihre
Ordner auflisten und Ihre Dateien lesen, einschließlich PDF- und Office-Dokumenten als Text, um Ihnen zu antworten. Er
verändert oder löscht sie nie; zum Erstellen von Dateien nutzt er den [Code Interpreter](../6_coding/).

## Gut zu wissen

- **Ihr Dateibereich wird zusammen mit Ihrem Chat-Konto eingerichtet.** Wenn My Files meldet, dass er noch nicht
  eingerichtet ist, öffnen Sie einmal den Chat.
- **Dateien bleiben erhalten.** Sie werden alle paar Minuten in den Speicher der Plattform kopiert; eine Datei, die Sie
  löschen, wird dort noch eine Woche aufbewahrt, bevor sie endgültig verschwindet.
- **Eine gemeinsame Sandbox.** Das Home jedes Benutzers ist getrennt, aber alle Benutzer teilen sich einen
  Sandbox-Container; siehe [Programmierung / Softwareentwicklung](../6_coding/), was das bedeutet.
