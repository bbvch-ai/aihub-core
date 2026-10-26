---
title: Jira aus einem Agent lesen
description: Lassen Sie einen Agent Tickets aus Jira Cloud oder Jira Data Center per JQL abfragen, mit Beschreibungen als lesbarem Text.
source_sha: 9ff76ca9c1a88e04e9bfd2b0f29317084e78f937ae2f964ac584fccbdf28996b
---

# Jira aus einem Agent lesen

Ein Agent, der mit aktuellen Jira-Daten arbeitet, etwa einer, der Release Notes für eine Fix-Version schreibt, fragt
Jira direkt ab. Core enthält dafür einen Jira-Client, der nur liest. Er funktioniert gleich gegen Jira Cloud und Jira
Data Center 11.3 und liest selbst keine Agent-Konfiguration: Ihr Agent bindet eine Verbindungskonfiguration ein und
übergibt sie.

## Die Verbindungskonfiguration

`JiraConnectionConfig` ist eine `StepConfig`, daher injiziert der Dispatcher sie in jeden Schritt, der sie als Parameter
deklariert.

| Feld          | Zweck                                                                                                   |
| ------------- | ------------------------------------------------------------------------------------------------------- |
| `base_url`    | Wo Jira erreichbar ist, z. B. `https://acme.atlassian.net` oder `https://jira.acme.ch/jira`.            |
| `deployment`  | `cloud` oder `data_center`. Bestimmt, wie sich der Agent anmeldet und wie Ergebnisse geblättert werden. |
| `email`       | Nur Jira Cloud: das Konto, zu dem das API-Token gehört.                                                 |
| `api_token`   | Ein Jira-Cloud-API-Token ohne Bereiche oder ein persönliches Zugriffstoken von Jira Data Center.        |
| `max_tickets` | Vom Deployment festgelegt (1'000): Eine Suche mit mehr Treffern schlägt fehl, statt gekürzt zu werden.  |

Das Token ist ein Passwortfeld. Alle, die den Agent nutzen, lesen, was dieses Konto lesen darf. Geben Sie dem Agent
deshalb ein eigenes Konto mit Lesezugriff, beschränkt auf die Projekte, die er braucht. Wie die Tokens erstellt werden,
ist bei der [Jira-Wissensquelle](../../../2_platform/8_knowledges/#jira-issues) beschrieben; dieselben Tokens
funktionieren hier.

## Tickets in einem Schritt finden

Fügen Sie die Konfiguration Ihrer Agent-Konfiguration hinzu und rufen Sie in einem Schritt
`JiraTicketSearch.find_tickets` auf. Die Methode gibt jedes passende Ticket zurück, folgt dabei dem Paging von Jira bis
zum Ende und sortiert nach Projekt und Nummer.

```python
from swiss_ai_hub.core.jira import JiraConnectionConfig, JiraJql, JiraTicketSearch


class ReleaseNotesAgentConfig(AgentConfig):
    jira: JiraConnectionConfig


class ReleaseNotesAgent(Agent):
    @step()
    async def collect_tickets(self, event: ReleaseRequestedEvent, jira: JiraConnectionConfig) -> TicketsFoundEvent:
        tickets = await JiraTicketSearch.find_tickets(
            jira,
            project_keys=["ENG", "SD"],
            clauses=['issuetype != "Sub-task"', f"fixVersion = {JiraJql.string_literal(event.version)}"],
        )
        return TicketsFoundEvent(keys=[ticket.key for ticket in tickets])
```

Jede Klausel wird in Klammern gesetzt und nach der Projekteinschränkung mit `AND` verbunden, sodass ein `OR` darin keine
anderen Projekte erreicht. Ein Wert aus einer Chat-Nachricht, wie die Version oben, muss durch
`JiraJql.string_literal()` gehen. Ungequotet in die Abfrage eingefügt, würde `2.4" OR project = HR` ein anderes Projekt
lesen.

Ein `JiraTicket` enthält `key`, `url`, `project`, `issue_type`, `status`, `summary`, `description`, `labels`,
`components` und `fix_versions`. Die Beschreibung ist Markdown, umgewandelt aus dem HTML, das Jira rendert.
Überschriften, Listen, Tabellen und Codeblöcke bleiben erhalten, und kein Rich-Text-JSON erreicht das Modell. Melder und
Bearbeiter werden nicht gelesen.

## Fehler

Jeder Fehler ist ein `JiraError` mit einer englischen Meldung, die nie das Token oder die Abfrage enthält. Fangen Sie
die Unterklassen ab, um Ihren Benutzern in ihrer Sprache zu sagen, was schiefgelaufen ist:

| Fehler                     | Ausgelöst, wenn                                                                                                           |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| `JiraConfigurationError`   | Ein Wert fehlt, die URL ins Innere der Plattform zeigt oder unter der URL keine Jira-REST-API antwortet.                  |
| `JiraAuthenticationError`  | Jira die Anmeldedaten ablehnt.                                                                                            |
| `JiraProjectNotFoundError` | Ein Projekt nicht existiert, das Konto es nicht sehen darf oder es umbenannt wurde (`renamed_to`).                        |
| `JiraInvalidQueryError`    | Jira die JQL ablehnt, z. B. ein unbekanntes Feld oder eine unbekannte Fix-Version; `problems` enthält Jiras eigene Worte. |
| `JiraTooManyTicketsError`  | Mehr Tickets passen als `max_tickets`.                                                                                    |
| `JiraRequestError`         | Jira mit einem anderen Fehler antwortet.                                                                                  |

Die Prüfungen laufen vor der Suche, in dieser Reihenfolge. Das ist wichtig, weil Jira Cloud eine ungültige Abfrage und
beide Editionen ein Projekt, das das Konto nicht sehen darf, mit null Tickets statt mit einem Fehler beantworten. Das
sähe sonst wie ein Release ohne Tickets aus.

## Hinweise zum Deployment

- **Netzwerk**: Ein Agent-Container braucht das Netzwerk `egress`, um Jira zu erreichen.
- **Internes Jira**: URLs, die ins Innere der Plattform zeigen (Docker-Servicenamen, `localhost`, private Adressen),
  werden abgelehnt, weil eine Agent-Administratorin oder ein Agent-Administrator die URL festlegt. Ein Jira, das nur im
  Firmennetz erreichbar ist, erlaubt ein Operator mit `JIRA_ALLOWED_PRIVATE_HOSTS` (kommagetrennte Hostnamen) auf dem
  Container des Agents.
- **Rate Limits**: Drosselung (429) und Gateway-Fehler werden einige Male wiederholt, unter Beachtung von `Retry-After`;
  eine Wartezeit über 30 Sekunden schlägt sofort fehl.
- **Cloud-Tokens**: API-Tokens mit Bereichen und Servicekonten werden noch nicht unterstützt, weil sie nur über das
  API-Gateway von Atlassian statt unter der Site-URL antworten.
