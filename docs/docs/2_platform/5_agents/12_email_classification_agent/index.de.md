---
title: E-Mail-Klassifizierungsagent
description: Ein Postfach-Agent, der jede ungelesene Nachricht liest, entscheidet, zu welcher Kategorie sie gehört, und sie im Ordner dieser Kategorie ablegt — mit einem Ausweichordner für alles, bei dem er unsicher ist.
---

# E-Mail-Klassifizierungsagent

Der **E-Mail-Klassifizierungsagent** macht aus einem gemeinsamen Postfach eine Warteschlange, die sich selbst sortiert.
Bei jedem Lauf liest er jede ungelesene Nachricht im Posteingang, entscheidet, zu welcher Ihrer Kategorien sie gehört,
und verschiebt sie in den Ordner dieser Kategorie. Alles, wozu keine Kategorie passt, landet in einem Ausweichordner,
statt in eine Kategorie geraten zu werden.

Wie der [E-Mail-Agent](../11_email_agent/) hat er **keine Chat-Oberfläche**. Sie konfigurieren ihn einmal in der
Admin-UI und lösen ihn programmatisch aus — durch einen anderen Workflow oder über die API.

::: warning Noch kein eingebauter Zeitplan
Der Agent hat keinen wiederkehrenden Auslöser, den Sie in der Admin-UI einstellen könnten. Jeder Lauf muss von aussen
gestartet werden — «sortiert sich selbst» heisst also «sortiert sich bei jedem Anstoss selbst». Bis die Planung
verfügbar ist, stossen Sie ihn aus dem an, was in Ihrer Umgebung ohnehin nach Zeitplan läuft.
:::

::: warning Er versendet niemals E-Mails
Der Agent spricht ausschliesslich IMAP — es gibt nirgends SMTP. Er liest, legt ab und erstellt Ordner. Er kann keine
Nachricht auf die Leitung geben. Das ist eine Design-Grenze, keine Einstellung.
:::

::: tip Die Kategorien gehören Ihnen, nicht uns
Es gibt keine eingebaute Taxonomie. Sie definieren die Kategorien und können jederzeit eine hinzufügen oder umbenennen —
ohne Deployment. Was die Klassifizierung überhaupt funktionieren lässt, ist die **Beschreibung**, die Sie zu jeder
schreiben (siehe unten).
:::

## Was er tut

```mermaid
flowchart TD
    A[Auslöser] --> B[Alle ungelesenen Nachrichten auflisten]
    B --> C{Ungelesene<br/>vorhanden?}
    C -- Nein --> D[Leeren Lauf melden, stoppen]
    C -- Ja --> E[Jede Nachricht abrufen<br/>+ Original archivieren]
    E --> F[Modell fragen, zu welcher<br/>Kategorie jede gehört]
    F --> G{Passt eine<br/>Kategorie?}
    G -- Ja --> H[In den Ordner der<br/>Kategorie ablegen]
    G -- Nein --> I[In den Ausweich-<br/>ordner ablegen]
    H --> J[Melden, wie viele je<br/>Kategorie abgelegt wurden]
    I --> J
```

1. **Auflisten.** Jede ungelesene Nachricht im Posteingang, älteste zuerst, bis zu **Max. ungelesene Nachrichten**.
2. **Abrufen und archivieren.** Jede Nachricht wird vollständig abgerufen. Ihre Anhänge und die Originalnachricht werden
   im Dateispeicher der Plattform abgelegt, sodass die vollständige E-Mail auch nach dem Verschieben erhalten bleibt.
3. **Klassifizieren.** Dem konfigurierten Modell werden Ihre Kategorienamen und -beschreibungen gezeigt; es wählt eine
   pro Nachricht — oder lehnt ab, wenn keine passt.
4. **Ablegen.** Jede Nachricht wird in den Ordner ihrer Kategorie verschoben. **Existiert der Ordner nicht, erstellt ihn
   der Agent** und abonniert ihn, damit er im Mail-Client sichtbar wird.
5. **Melden.** Der Lauf hält fest, wie viele Nachrichten abgelegt wurden und wie viele auf jede Kategorie entfielen.

::: details Warum ein erneuter Lauf unbedenklich ist
Das Ablegen selbst verhindert Doppelarbeit. Jede Nachricht — sicher eingeordnet oder nicht — verlässt den Posteingang,
sodass die Auflistung des nächsten Laufs sie schlicht nicht mehr sehen kann. Es gibt kein Flag, das aus dem Takt geraten
könnte, und nichts aufzuräumen. Bricht ein Lauf auf halbem Weg ab, bleiben die bereits abgelegten Nachrichten abgelegt,
und der Rest liegt weiterhin ungelesen bereit für den nächsten Lauf.
:::

::: details Die Nachricht bleibt ungelesen
E-Mails werden mit `BODY.PEEK` gelesen, der Agent markiert also nie etwas als gesehen. Wer den Ordner `Support` öffnet,
sieht weiterhin echte ungelesene Post — der Agent hat sie sortiert, nicht erledigt.
:::

## Konfiguration

Erstellen Sie in der Admin-UI ein Profil aus der Vorlage **E-Mail-Klassifizierungsagent**.

### Postfachverbindung

Dieselben Felder wie beim [E-Mail-Agenten](../11_email_agent/): Host, Port, Benutzername, Passwort, TLS,
Posteingangsordner und **Max. ungelesene Nachrichten**. Einen „Verarbeitet-Ordner" gibt es hier nicht — der
Klassifizierer entscheidet, wohin jede Nachricht geht.

### Kategorien

Eine wiederholbare Liste. Fügen Sie einen Eintrag pro Kategorie hinzu:

| Feld                   | Beschreibung                                                                                    |
| ---------------------- | ----------------------------------------------------------------------------------------------- |
| **Kategorie**          | Ein kurzer Name, z. B. `support_request`. Muss eindeutig sein.                                  |
| **Zielordner**         | Wohin E-Mails dieser Kategorie abgelegt werden. Wird bei Bedarf erstellt. Muss eindeutig sein.  |
| **Was gehört hierher** | Eine Beschreibung der Art von E-Mails, die in diese Kategorie gehört. **Das liest das Modell.** |

::: tip Schreiben Sie die Beschreibung für eine neue Kollegin, nicht für eine Suchmaschine
Dieses Feld leistet die eigentliche Arbeit. Ordnernamen allein können eine *Informationsanfrage* nicht von einer
*Supportanfrage* trennen — eine Beschreibung schon: „wir können das lösen, indem wir eine Auskunft geben" gegenüber „das
erfordert eine Handlung unseres Teams". Beschreiben Sie die **Absicht** der Absenderin und was die Bearbeitung bedeuten
würde. Stichwortlisten funktionieren deutlich schlechter als ein klarer Satz darüber, wozu die Kategorie da ist.
:::

::: warning Verschachtelte Ordnernamen nutzen das Trennzeichen *Ihres* Servers
Ein Zielordner wie `Triage/Support` ergibt nur auf Servern eine echte Ordnerstruktur, deren Trennzeichen `/` ist — etwa
Gmail. Auf einem Server mit `.` entstünde ein einzelner flacher Ordner mit dem Namen `Triage/Support`; schreiben Sie
dort stattdessen `Triage.Support`. Abgelegt wird die Post in beiden Fällen korrekt, eine Baumstruktur erhalten Sie aber
nur mit dem passenden Trennzeichen. Im Zweifel verwenden Sie flache Namen wie `Support` und `Invoices`.
:::

### Klassifizierer

| Feld                        | Standard                | Beschreibung                                                                           |
| --------------------------- | ----------------------- | -------------------------------------------------------------------------------------- |
| **Ausweichordner**          | `Uncategorised`         | Wohin E-Mails ohne passende Kategorie gehen. Nie geraten, nie im Posteingang belassen. |
| **Klassifizierungsmodell**  | *(leer)*                | Das klassifizierende Modell. Leer lassen, um das Hauptmodell des Agenten zu verwenden. |
| **Klassifizierungs-Prompt** | *(sinnvoller Standard)* | Anweisungen, wie das Modell auswählt.                                                  |

::: details Der Weg in den Ausweichordner
Das Modell hat genau einen Ausweg: Es kann ausdrücklich sagen, dass **keine der Kategorien passt**. Dann geht die
Nachricht in den Ausweichordner statt in einen Kategorieordner.

Eine frühere Fassung liess das Modell zusätzlich seine eigene Konfidenz bewerten und leitete alles unterhalb einer
Schwelle um. Diese Einstellung wurde entfernt. Ein selbst gemeldeter Wert entsteht im selben Zug wie die Antwort, statt
gemessen zu werden — er trägt also nichts bei, was in der Wahl nicht ohnehin steckt. Über die Chat-Modelle der Plattform
hinweg an einer bewusst mehrdeutigen Nachricht gemessen, fing die ausdrückliche Ablehnung sie in vier von fünf Fällen
ab, während die Schwelle kein einziges Mal griff; das eine Modell, das falsch ablegte, tat dies mit 0.95 Konfidenz.

Die praktische Folge: **Ihre Kategoriebeschreibungen sind das Sicherheitsnetz, nicht ein Regler.** Landet Post im
falschen Ordner, schärfen Sie die Beschreibungen der beiden verwechselten Kategorien.

## Erste Schritte

1. **Beginnen Sie mit zwei oder drei Kategorien**, nicht mit fünfzehn. Breite, klar unterscheidbare Töpfe werden weit
   zuverlässiger klassifiziert als eine lange Liste überlappender — aufteilen können Sie später.
2. **Lassen Sie ihn die Ordner erstellen.** Verweisen Sie auf noch nicht existierende Ordner und lassen Sie den ersten
   Lauf sie anlegen; so stimmen die Namen exakt überein.
3. **Verfolgen Sie die ersten Läufe in der Ereignis-Timeline.** Bei jeder Nachricht sind die gewählte Kategorie und die
   Begründung des Modells sichtbar. Diese Begründung ist der schnellste Weg zu einer Beschreibung, die eine
   Überarbeitung braucht.
4. **Beheben Sie Fehlablagen in den Beschreibungen.** Sie sind der einzige Hebel — und der richtige: fast jede
   Fehlablage geht auf zwei Kategorien mit überlappenden Beschreibungen zurück.
5. **Danach stossen Sie ihn regelmässig an** — aus dem, was bei Ihnen ohnehin nach Zeitplan läuft — und der Posteingang
   leert sich von selbst.

## Was er *nicht* tut

- **Er versendet nie und löscht nie.** Verschieben verlagert eine Nachricht; nichts verlässt das Postfach.
- **Er entwirft keine Antworten.** Das ist eine eigene Fähigkeit — siehe [E-Mail-Agent](../11_email_agent/).
- **Er liest zum Klassifizieren keine Anhänge.** Die Klassifizierung nutzt Kopfzeilen und den Textkörper. Anhänge werden
  archiviert, beeinflussen die Kategorie aber nicht.
- **Er hat keine Chat-Oberfläche** und keine Wissensdatenbank.
- **Er überspringt keine Nachricht, die er nicht verarbeiten kann.** Ein Lauf ist ganz oder gar nicht: Scheitert die
  Klassifizierung einer Nachricht, wird nichts aus diesem Stapel abgelegt und der ganze Stapel im nächsten Lauf erneut
  versucht. Das verhindert, dass eine vorübergehende Störung Post in den Ausweichordner streut — bedeutet aber, dass
  eine dauerhaft unverarbeitbare Nachricht das Postfach blockiert, bis Sie sie von Hand herausnehmen. Achten Sie auf
  Läufe, die jedes Mal mit einem Fehler und ohne Ablage enden.

::: warning Eingehende E-Mails sind nicht vertrauenswürdig Jede und jeder kann Ihrem Postfach alles schicken, und der
Textkörper geht in den Prompt des Modells. Der Agent ist so gebaut, dass der schlimmste Fall begrenzt bleibt: Das Modell
wählt aus **Ihrer** Kategorienliste und kann immer nur eine Position in dieser Liste zurückgeben — eine Nachricht mit
eingebetteten Anweisungen kann also keinen Zielordner erfinden und den Agenten zu nichts anderem bringen als zum Ablegen
von Post. Der PII-Schutz der Plattform anonymisiert personenbezogene Daten am LLM-Gateway. Behandeln Sie den Ordner, in
dem eine Nachricht gelandet ist, dennoch als Vorschlag, nicht als Urteil.
:::
