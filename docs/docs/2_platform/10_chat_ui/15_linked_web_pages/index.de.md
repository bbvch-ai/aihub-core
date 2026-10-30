---
title: Verlinkte Webseiten
description: Agenten lesen die Webseiten, die Sie in einer Nachricht verlinken, antworten daraus, zitieren sie und nennen Ihnen die Seiten, die sie nicht lesen konnten.
source_sha: d0d7a5cec0d895777f36c947d41d6f338e7f5e0d4e5a3c86d2c6e59142866277
---

# Verlinkte Webseiten

Fügen Sie einen Link in eine Nachricht an einen Agenten ein oder hängen Sie eine Seite mit `#` an, und der Agent liest
die Seite und antwortet daraus. Jede verwendete Seite wird als Quelle zitiert, und eine Seite, die er nicht lesen
konnte, wird in der Antwort mit dem Grund genannt, statt erraten zu werden.

::: tip Nicht dasselbe wie die Websuche
Hier wählen Sie die Seiten. Die [Websuche](../5_websearch/) lässt einen Chat mit einem reinen Modell selbst nach Seiten
suchen und wird bei Agenten nicht angeboten.
:::

## Welche Agenten Links lesen

Das Lesen von Links ist eine Einstellung pro Agentenprofil und **standardmässig ausgeschaltet**: Ein Admin schaltet im
Profil **Read Linked Web Pages** ein. Verfügbar ist sie beim Instructed Assistant, beim Document Intelligence Assistant,
beim Company Knowledge Agent und beim Universal Agent. Der [Webseiten-Assistent](../../5_agents/15_web_page_assistant/)
liest Links immer; dafür ist er da.

## Seiten verlinken

Zwei Wege, die gleich gelesen werden:

- **Link einfügen**, an beliebiger Stelle in Ihrer Nachricht:
  `What does https://example.com/pricing say about discounts?` Jeder Link in der Nachricht wird gelesen, bis zum Limit
  des Profils (standardmässig 5), nicht nur der erste.
- **Mit `#` anhängen**: Tippen Sie `#`, fügen Sie die Adresse ein und wählen Sie sie aus. Die Seite erscheint als Anhang
  über der Nachricht, und der Link bleibt aus dem Nachrichtentext heraus.

Gelesen werden nur `http://`- und `https://`-Links.

## Was Sie sehen

Während die Seiten laden, zeigt der Chat **Reading the linked web pages**. Sind sie gelesen, wechselt der Status zu
**Read 3 web pages** (bzw. der entsprechenden Anzahl), jede Seite erscheint als Quelle mit Titel und Adresse, und die
Antwort zitiert die verwendeten Seiten mit nummerierten Chips. Event-Verlauf und Trace des Agenten führen die gelesenen
und die fehlgeschlagenen Seiten auf.

## Wenn eine Seite nicht gelesen werden kann

Der Status nennt die fehlgeschlagenen Links, zum Beispiel **Could not read: https://example.com/members**, und die
Antwort sagt, welche Seiten nicht gelesen werden konnten, und schlägt vor, deren Text in den Chat einzufügen. Eine
Seite, die nicht gelesen wurde, beschreibt sie nicht.

| Grund                        | Bedeutung                                                                                   |
| ---------------------------- | ------------------------------------------------------------------------------------------- |
| Keine gültige Webadresse     | Der Link ist fehlerhaft.                                                                    |
| Kein http- oder https-Link   | Andere Schemas wie `ftp:` oder `file:` werden nie geöffnet.                                 |
| Interne oder private Adresse | Der Link zeigt in ein privates Netzwerk, etwa auf eine Intranet-Adresse. Siehe unten.       |
| Seite existiert nicht        | Die Website antwortete mit 404 oder 410.                                                    |
| Zugriff verweigert           | Ein Login, eine Paywall oder ein Bot-Schutz stand im Weg (401, 403, 429, 451).              |
| Fehler der Website           | Jede andere Fehlerantwort der Website.                                                      |
| Dauerte zu lange             | Die Seite lud nicht innerhalb des Zeitlimits des Profils (standardmässig 15 Sekunden).      |
| Keine Webseite               | Der Link führt zu einem PDF, einem Bild oder einem Download. Hängen Sie die Datei an.       |
| Kein lesbarer Text           | Die Seite lud, hatte aber keinen Haupttext, wie viele Video- und App-Seiten.                |
| Über dem Link-Limit          | Die Nachricht hat mehr Links, als das Profil auf einmal liest; der Rest wird nicht gelesen. |

::: warning Wenn Open WebUI eine `#`-Seite nicht laden kann
Open WebUI lädt eine mit `#` angehängte Seite selbst, sobald Sie sie auswählen. Schlägt das fehl, zeigt Open WebUI eine
eigene Fehlermeldung und entfernt den Anhang, sodass der Agent ihn nie sieht. Fügen Sie den Link stattdessen in die
Nachricht ein; dann liest der Agent ihn und meldet einen Fehler selbst.
:::

## Wenn das Lesen von Links ausgeschaltet ist

Ein Agent, dessen Profil keine Links liest, öffnet sie nicht und zeigt keinen Lesestatus. Hängt Ihre Frage von einer
verlinkten Seite ab, sagt er, dass er keine Links öffnen kann, und bittet Sie, den Text der Seite einzufügen.

## Beim Universal Agent

Der Universal Agent entscheidet selbst, ob er eine Seite braucht. Er darf **nur die Seiten lesen, die Sie verlinkt
haben**: Versucht das Modell, eine andere Adresse zu öffnen, etwa einen Link, den es in einer Seite gefunden hat, wird
der Aufruf abgelehnt. So kann eine in einer Seite oder Datei versteckte Anweisung Ihre Unterhaltung nicht an eine
Website ihrer Wahl senden.

## Limits

Seiten werden gelesen, bevor die Antwort beginnt, und gehen in den Prompt des Modells ein; jede verlängert also Dauer
und Kosten der Antwort. Ein Profil legt fest, wie viele Links einer Nachricht gelesen werden, wie lange eine Seite laden
darf und wie viel einer Seite das Modell erhält (standardmässig 20'000 Zeichen, etwa 5'000 Tokens; eine längere Seite
wird an einem Absatzende gekürzt). Mehrere lange Seiten ergeben einen grossen Prompt, und manche Modelle beantworten
grosse Prompts deutlich langsamer.

## Sicherheit

- **Interne Adressen werden abgelehnt.** Jede Anfrage einer Seite, einschliesslich Weiterleitungen und der Dateien, die
  sie lädt, wird zuerst geprüft, und Adressen in privaten Netzwerken oder mit internen Namen werden abgelehnt. Der
  Browser erreicht das Internet nur über einen filternden Proxy, der jeden Host selbst auflöst und alles ablehnt, was
  keine öffentliche Adresse ist.
- **Der Browser ist isoliert.** Seiten werden vom plattformeigenen Browser-Dienst geladen, der in einer eigenen
  Netzwerkzone liegt und die internen Dienste der Plattform nicht erreichen kann. Siehe
  [Netzwerkisolation](../../2_architecture/4_network_isolation/).
- **Seiten sind nicht vertrauenswürdig.** Das Modell wird angewiesen, den Inhalt einer Seite nur als Information zu
  nutzen und nie Anweisungen zu befolgen, die darin stehen.
- **Jeder Abruf wird getraced.** Welche Seiten gelesen wurden und welche aus welchem Grund fehlschlugen, wird in den
  Events des Agenten und im Trace festgehalten.
